# How this repository was made (Fortaleza)

This file is written by the build on 2026-10-31, the day the source data was retrieved.

## Sources

| Source | Address | Retrieved | Licence |
| --- | --- | --- | --- |
| Câmara Municipal de Fortaleza, SAPL: Texto Articulado of the Lei Orgânica, one view per period of vigência | <https://sapl.fortaleza.ce.leg.br/norma/5257> | 2026-10-31 | Text: Câmara Municipal de Fortaleza, SAPL (Sistema de Apoio ao Processo Legislativo), Lei Orgânica do Município de Fortaleza, sapl.fortaleza.ce.leg.br. Lei 9.610/1998 art. 8 IV: the texts of laws and other official acts are not protected by copyright. Non-official text: only the Diário Oficial do Município is authoritative. |

Every word of law in this repository comes from these sources. Lexifina reads them and records each act's dated versions, and the laws that made each change, in one corpus file. This repository is built from that file.

## What is in it

| Act | Title | Versions | Span |
| --- | --- | ---: | --- |
| `lei-organica` | Lei Orgânica do Município de Fortaleza | 27 | 2006-12-15 to 2025-06-30 |

The build made 25 commits:

| Commits | Kind |
| ---: | --- |
| 1 | first version of an act |
| 23 | one law on its in-force day |
| 1 | changes no amendment note explains, credited to the publisher |

Other counts:
- 0 commits on the branch `futuro`: laws not yet in force on 2026-10-31.
- 0 commits dated 1 January 1970: in force before 1970, with the real day in their `In-force` trailer.
- 26 laws in the record.
- 49 tags.

## Dates

Each commit is dated at noon (America/Fortaleza) on the day the change took effect. The other dates, enacted and published, are trailers.

When a law gives no date of its own, the default rule applies: The Lei Orgânica and its amendments are promulgated by the Mesa da Câmara and take effect as they state; this record dates each version by the first day of vigência SAPL gives it. https://sapl.fortaleza.ce.leg.br/norma/5257

## How the history is built

`tools/build.py` turns the corpus into this history in one pass: one commit per law, on the day it took effect. The same corpus always gives the same commit hashes. `tools/check_repo.py` reads every version back from git and compares it with the corpus. `tools/on.py` shows the law as it stood on any date. The corpus format is described in `tools/SCHEMA.md`.

- Corpus: sha256 `3fe3c3f1e85d408704b8e1db7ff37d1c57b353605482a8c931c4a0cd683b52c8` (408499 bytes).
- Builder blob hashes (`git hash-object`): `build.py` `a4faa25af85facb64b956b372f6b528aafdd7ec1`, `check.py` `3d00541d258745461ab52b1b0cb4e1716a27a95d`, `on.py` `644a6c0857fbcc72562032b58d57aa113fee0641`.
- Python 3.12.10; git version 2.46.0.windows.1.

## Checks

27 versions of 1 acts read back from git on the day each took effect and on the day before: 0 mismatches. Trailers: 0 commits whose trailers git cannot parse. Health: 0 merge commits on main, 0 commit dates that go backwards, 0 commits dated after the build.

No second build of this corpus has been compared yet.

## Decisions made by hand

- Each version is one SAPL "vigência" view of the Lei Orgânica's Texto Articulado: the text in force from the view's first day, dated by that day and credited to the act SAPL says gave it ("Dada por ..."); the first view (from 15 December 2006) is credited to the Lei Orgânica itself. Where two views start on the same day (two amendments of the same date), both are kept, in SAPL order, as two versions of that day. Each unit that differs from the view before is credited to the act that gave the view.
- The last version is the text SAPL shows as in force now (the norma page, "Vigência a partir de 30 de Junho de 2025", "Dada por" Emenda à Lei Orgânica nº 25). Where SAPL starts a period without naming an amending act (from 27 August 2021), the units that changed are left uncredited and committed as publisher commits, not guessed.
- Each provision is one line: its label ("Art. 1º.", "§ 1º", "XV –") followed by its text; table rows are one line each, cells separated by " | ". Notes SAPL keeps under a provision or links into it ("Inclusão feita pelo ..."), provisions it marks as superseded and the amending acts own blocks it shows inside the text are left out.
- One file per Art.; headings stand above the first article under them; the "Ato das Disposições Orgânicas Transitórias", numbered from 1 again, is adt-*. "000-titulo" holds the preamble.

## What AI did and did not do

The scripts that read the sources and build this repository were written by Claude Code running Claude Opus 5.5 (`claude-opus-5-5`) under Lexifina's direction.

No model wrote, translated or corrected legal text. No model runs at build time. Every word of law in this repository comes from the official sources above.

The commit messages are written by `build.py` from the source data.

Model use at data-build time:
- Claude Code (claude-opus-5-5) wrote Lexifina's code and chose the sources. No model output is used as legal text or dates: every word comes from the SAPL pages.
