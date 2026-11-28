# chgk-skills

Claude Code skills for editors and authors of «Что? Где? Когда?» (sport ЧГК) questions.

| Skill | Status | What it does |
|---|---|---|
| `chgk-assess` | draft | Editorial review of a question or packet: dual answers, repeats, logic, facts, wording, verdict and concrete edits |
| `chgk-format` | planned | Formatting: answer, зачёт/незачёт, комментарий, sources, author (draft material in `plugins/chgk-editor/skills/chgk-format/references/format.md`) |
| `chgk-test` | planned | Blind testing with separate "team" agents that never see the answer |
| `chgk-improve` | draft | Work-in-progress question: finds what the question is for, separates blockers from weaknesses, offers 4–6 improvement options with full text, cost and risks |
| `chgk-candle` | draft | Repeat (свечка) check on gotquestions.online: key queries approved by the author, polite search (1 request/min), verdict on each predecessor |
| `chgk-ideas` | planned | Source material and angles for new questions, with real sources |

The skills work out of the box with the public principles in `plugins/chgk-editor/skills/chgk-assess/references/principles.md` (codes О1–О8, Ж1–Ж9, П1–П4, А1–А4).
The general standard behind them, with details and sources, is in `references/criteria.md` next to it.
Personal editorial principles can override them (see "Personal principles" below).

## Install

```
/plugin marketplace add harlin/chgk-skills
/plugin install chgk-editor@chgk-skills
```

## Personal principles

`chgk-assess` and `chgk-improve` also load a skill named `chgk-principles` if one is installed, or a file at `$CHGK_PRINCIPLES`.
A personal principle with the same code replaces the public one; codes missing from the personal file come from the public `principles.md`.
You can add your own codes or sections (for example, minor weaknesses that lower the category slightly).

## Never commit unplayed questions

This repository is public. Evals and examples must use only questions that have already been played and published.

## License

Apache License 2.0, see `LICENSE`. Earlier versions were released under GPL-3.0.

Played questions quoted as examples belong to their authors and are not covered by this license; each quote names its author or tournament.
