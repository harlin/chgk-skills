# chgk-skills

Claude Code skills for editors and authors of «Что? Где? Когда?» (sport ЧГК) questions.

| Skill | Status | What it does |
|---|---|---|
| `chgk-assess` | draft | Editorial review of a question or packet: dual answers, repeats, logic, facts, wording, verdict and concrete edits |
| `chgk-format` | planned | Formatting: answer, зачёт/незачёт, комментарий, sources, author (draft material in `skills/chgk-format/references/format.md`) |
| `chgk-test` | planned | Blind testing with separate "team" agents that never see the answer |
| `chgk-improve` | draft | Work-in-progress question: finds what the question is for, separates blockers from weaknesses, offers 2–4 improvement options with full text, cost and risks |
| `chgk-candle` | draft | Repeat (свечка) check on gotquestions.online: key queries approved by the author, polite search (1 request/min), verdict on each predecessor |
| `chgk-ideas` | planned | Source material and angles for new questions, with real sources |

The general standard lives in `plugins/chgk-editor/skills/chgk-assess/references/criteria.md`.
Personal editorial principles can override it (see "Personal principles" below).

## Install

```
/plugin marketplace add harlin/chgk-skills
/plugin install chgk-editor@chgk-skills
```

## Personal principles

`chgk-assess` loads a skill named `chgk-principles` if one is installed, or a file at `$CHGK_PRINCIPLES`.
Personal rules take precedence over the general standard.

## Never commit unplayed questions

This repository is public. Evals and examples must use only questions that have already been played and published.
