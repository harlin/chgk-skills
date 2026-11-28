#!/usr/bin/env python3
"""Polite search on gotquestions.online for candle (repeat) checks.

Usage:
    python3 -I gq_search.py [--page N] [--full] QUERY [QUERY ...]

For each query prints one JSON object (one line) with the total hit count and
the questions of the requested results page (18 per page), compactly:
id, url, pack title, pack end date, take rate, answer, zachet, text, comment
(trimmed unless --full) and the fields where the match was found.

Politeness rules (do not loosen them):
- at most one request per MIN_INTERVAL seconds, shared by every chgk-skills
  tool through ~/.cache/chgk-skills/gq_last_request.sqlite;
- answers are cached in ~/.cache/chgk-skills/gq_search/, a repeated query
  never goes to the site;
- an honest User-Agent, no browser imitation, no retries;
- on a non-200 status, a challenge page or a page without search data the
  script stops at once (exit code 2) and the remaining queries are not sent.

Only the Python standard library is used.
"""

import hashlib
import html
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SEARCH_URL = "https://gotquestions.online/search?{}"
QUESTION_URL = "https://gotquestions.online/question/{}"
MIN_INTERVAL = 60  # seconds between requests to the site
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) chgk-skills-fetcher (personal research, 1 req/min)"
CACHE_ROOT = os.path.join(os.path.expanduser("~"), ".cache", "chgk-skills")
STATE_DB = os.path.join(CACHE_ROOT, "gq_last_request.sqlite")
LOCK_TIMEOUT = 600  # seconds to wait for other chgk-skills tools to finish their turn
CACHE_DIR = os.path.join(CACHE_ROOT, "gq_search")
TRIM = 300


class Wall(Exception):
    """The site refused us or served something unexpected. Do not retry."""


def wait_for_slot():
    # The write transaction spans read, sleep and write, so two tools started
    # at once cannot both see the same old timestamp and hit the site together.
    # SQLite does the cross-process locking the same way on every OS, makes
    # the others wait (up to LOCK_TIMEOUT) and drops the lock if we crash.
    os.makedirs(CACHE_ROOT, exist_ok=True)
    db = sqlite3.connect(STATE_DB, timeout=LOCK_TIMEOUT, isolation_level=None)
    try:
        db.execute("BEGIN IMMEDIATE")
        db.execute("CREATE TABLE IF NOT EXISTS slot (last REAL NOT NULL)")
        row = db.execute("SELECT max(last) FROM slot").fetchone()
        last = row[0] if row and row[0] is not None else 0.0
        delay = last + MIN_INTERVAL - time.time()
        if delay > 0:
            print(f"waiting {delay:.0f}s (1 request per minute)", file=sys.stderr, flush=True)
            time.sleep(delay)
        db.execute("DELETE FROM slot")
        db.execute("INSERT INTO slot VALUES (?)", (time.time(),))
        db.execute("COMMIT")
    except sqlite3.OperationalError as e:
        raise Wall(f"could not take the rate-limit lock ({e})")
    finally:
        db.close()


def fetch(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "text/html", "Accept-Language": "ru"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            if r.status != 200:
                raise Wall(f"HTTP {r.status}")
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raise Wall(f"HTTP {e.code}") from None
    except urllib.error.URLError as e:
        raise Wall(f"network error: {e.reason}") from None


def parse(page):
    low = page.lower()
    if any(s in low for s in ("captcha", "cf-challenge", "challenge-platform", "just a moment")):
        raise Wall("challenge page")
    chunks = re.findall(r'self\.__next_f\.push\(\[1,(".*?")\]\)</script>', page, flags=re.S)
    payload = "".join(json.loads(c) for c in chunks)
    key = '"initialData":'
    i = payload.find(key)
    if i < 0:
        raise Wall("no search data in the page (layout changed or blocked)")
    data, _ = json.JSONDecoder().raw_decode(payload, i + len(key))
    if "questions" not in data:
        raise Wall("unexpected search data (layout changed)")
    return data


def cache_path(query, page):
    h = hashlib.sha1(f"{query}\n{page}".encode("utf-8")).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"{h}.json")


def search(query, page=1):
    path = cache_path(query, page)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f), True
    params = {"search": query}
    if page > 1:
        params["page"] = page
    wait_for_slot()
    data = parse(fetch(SEARCH_URL.format(urllib.parse.urlencode(params))))
    data["_query"], data["_page"] = query, page
    data["_fetched_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return data, False


def plain(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def trim(s, full):
    s = (s or "").strip()
    return s if full or len(s) <= TRIM else s[:TRIM] + "…"


def compact(q, highlights, full):
    pack = (q.get("tour") or {}).get("pack") or {}
    hl = highlights.get(str(q["id"])) or {}
    return {
        "id": q["id"],
        "url": QUESTION_URL.format(q["id"]),
        "pack": pack.get("title"),
        "date": (pack.get("endDate") or pack.get("startDate") or "").lstrip("$D")[:10],
        "take": [c for c in (q.get("complexity") or []) if c],
        "teams": q.get("teamsCount") or None,
        "answer": q.get("answer"),
        "zachet": q.get("zachet") or None,
        "text": trim(q.get("text"), full),
        "razdatka": trim(q.get("razdatkaText"), full) or None,
        "comment": trim(q.get("comment"), full),
        "matched_in": sorted(hl.keys()),
        "match": {k: trim(plain(v), False) for k, v in hl.items() if k in ("answer", "zachet")},
    }


def main(argv):
    # Windows consoles default to a legacy code page and cannot print Cyrillic.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    full, page, queries = False, 1, []
    it = iter(argv)
    for a in it:
        if a == "--full":
            full = True
        elif a == "--page":
            n = next(it, "")
            if not n.isdigit() or int(n) < 1:
                sys.exit(f"--page needs a positive number, got {n!r}\n\n{__doc__}")
            page = int(n)
        else:
            queries.append(a)
    if not queries:
        sys.exit(__doc__)
    for qs in queries:
        try:
            data, cached = search(qs, page)
        except Wall as w:
            print(f"STOP on query {qs!r}: {w}. Not retrying; the remaining queries were not sent.",
                  file=sys.stderr)
            sys.exit(2)
        hl = data.get("highlights") or {}
        print(json.dumps({
            "query": qs,
            "page": data.get("page"),
            "total": data.get("total"),
            "totalPages": data.get("totalPages"),
            "cached": cached,
            "questions": [compact(q, hl, full) for q in data["questions"]],
        }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
