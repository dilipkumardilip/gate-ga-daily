# GA Daily — 60-day GATE General Aptitude test series

30 GATE-level GA questions a day for 60 days (1,800 questions), in a plain HTML/CSS/JS site. Progress is saved in your browser (localStorage).

## Use it
- **Quickest:** double-click `site/index.html` (works offline except the web fonts).
- **Local server:** `python3 -m http.server 8790 --directory site` → http://localhost:8790
- Day 1 = the start date in Settings (default: the day you first open the site). All days are open; today's is highlighted.
- Settings → Export progress makes a JSON backup, and Import restores it (use this to move between browsers/devices).

## Each day
- 30 questions · 45 marks · 60 min (changeable). Q1–15 are 1-mark, Q16–30 are 2-mark, like GATE's Q1–5 / Q6–10.
- 9 Verbal · 13 Quant · 6 Analytical · 2 Spatial (GATE DA ratios × 3). MCQ, MSQ and NAT; GATE negative marking (−1/3, −2/3) on MCQs only.
- About 4–5 real GATE PYQs per day. Days 58–60 contain the complete GA sections of GATE DA 2024, 2025 and 2026.
- Difficulty rises over the 60 days (Foundation → GATE standard → Advanced).
- After submitting: score, section/topic breakdown, every question with its solution, and a "why did I miss it" note box. **Mistakes** collects wrong and skipped questions for instant-feedback re-practice. **Progress** shows the score trend and your weakest topics.

## How the questions were made and checked
- `bank/PYQ.jsonl`: 287 real GATE GA PYQs (2010–2026, all papers incl. DA 2024–26), with official keys that were re-derived earlier in `Notes/_tools/GA_src/research`.
- `bank/QN*.jsonl`, `VB*`, `AN*`, `SP*`: 1,700 original questions written to the brief in `BRIEF.md`, using the GA handbook and the GO Classes formula sheet as references.
  - Every quant question, and every analytical/spatial question that can be brute-forced, has `verify` code that recomputes the answer from scratch (`tools/validate.py` runs it, along with KaTeX and schema checks).
  - Every original question was then **solved blind** by a separate agent that never saw the key (`SOLVER_BRIEF.md`, `review/blind/`). Answers disagreed with the key on 10 of 1,700 questions; each was reviewed and the key was correct every time. 5 questions were reworded or redrawn for clarity (`review/fixes.jsonl`). Decisions are logged in `review/adjudication.md`.
- `tools/assemble.py` builds `site/data/days/dayNN.js` from the bank (`review/assembly_report.md` shows each day's composition). 187 spare questions are left in the bank, unused.

## Rebuild after editing questions
```bash
tools/.venv/bin/python -I tools/validate.py --all
tools/.venv/bin/python -I tools/assemble.py
```
Fixes go in `review/fixes.jsonl` (replaces a bank item by id); drops go in `review/drop.txt`.
Note: re-assembling may move questions between days, so do it before you start the 60 days, not halfway through.
