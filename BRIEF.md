# Question-writer brief — GATE 2027 General Aptitude daily tests

You are writing questions for a personal daily-test website: **60 days × 30 GATE-level General Aptitude (GA) questions** for a GATE 2027 DA aspirant targeting 15/15 in GA. Real PYQs are added separately; you write **original** questions of real GATE GA standard. Quality and correctness matter more than speed: a wrong key or an ambiguous question is worse than a missing one.

Root: `/Users/dilipkumar/Downloads/GATE2027/Aptitude/DailyTest/` (paths below are relative to it).

## 1. What "GATE level" means here
- Look at real GATE GA questions before you start: `/Users/dilipkumar/Downloads/GATE2027/Notes/_tools/GA_src/research/recent_ga.md` (2021–26, best style reference), `classic_ga.md` (2010–20) and `da_ga.md` (DA 2024–26). Read the sections for your topics.
- Topic coverage, formulas, standard traps: the handbook chapters in `/Users/dilipkumar/Downloads/GATE2027/Aptitude/build/chapters/*.md` (read the ones for your topics) and the GO Classes formula sheet `/Users/dilipkumar/Downloads/GATE2027/Aptitude/GO_Classes_Apti.pdf` (Read with `pages`, quant pp. 3–42).
- 1-mark: direct, 1–2 reasoning steps, ~1–1.5 min. 2-mark: 3–5 steps, combines ideas or needs careful reading, ~2–3 min. Not CAT-monster level, not school-trivial.
- Write in the GATE voice: short precise stems, "Select the most appropriate option…", "The value of … is", "Which one of the following …". Indian context is fine (₹, km, names like Ravi, Meera), no current affairs, no specialist knowledge.
- **Original**: do not copy a PYQ or a handbook example. Use the same *patterns* with new numbers, new contexts, new twists.

## 2. Hard quality rules
1. Exactly **one** defensible answer for MCQ (MSQ: the stated set exactly; NAT: the stated range). If a smart examiner could argue for a second option, rewrite.
2. Distractors must be plausible — each should be the result of a specific common mistake (wrong base for %, forgetting a case, off-by-one, misreading 'not'). No joke options, no "all/none of the above".
3. All numbers must work out cleanly (GATE has only a basic virtual calculator).
4. Balance the MCQ answer letters A/B/C/D roughly equally across your file (don't let the right answer always be the computed-first value; shuffle).
5. Every question stands alone, except a data set / passage shared by a `group` (see §4).
6. Units and wording precise: "at least", "exactly", "not", "maximum", "how many more" — be explicit.
7. Verbal: standard modern English usage only; avoid items hinging on British vs American spelling, rare idioms, or contested usage. State the rule in the solution.
8. Before writing each item, solve it yourself independently; after writing, re-read the stem as a student would.

## 3. Mix targets (over your whole file)
- difficulty (1 = easy GATE, 2 = standard GATE, 3 = hard GATE): about **30% / 45% / 25%**.
- marks: Quant ≈ 45% 1-mark / 55% 2-mark; Verbal ≈ 55/45; Analytical and Spatial ≈ 50/50. Difficulty 1 is usually 1-mark, 3 is usually 2-mark.
- type: MCQ ≈ 80–85%, MSQ ≈ 7–10% (one or more correct; answer is a list), NAT ≈ 8–10% (numeric entry, no options; mainly Quant/Analytical — Verbal: MCQ/MSQ only).

## 4. Format — one JSON object per line (JSONL) in your file `bank/<PREFIX>.jsonl`
```json
{"id":"QN1-001","section":"Quant","topic":"Number System","subtopic":"unit digit","difficulty":2,"marks":1,"type":"MCQ",
 "q":"The unit digit of $7^{2027}$ is","options":["1","3","7","9"],"answer":"B",
 "solution":"Unit digits of powers of 7 repeat 7, 9, 3, 1 (cycle 4).<br>$2027 = 4\\cdot 506 + 3$, so the digit is the 3rd in the cycle: <b>3</b>.<br>Trap: using $2027 \\bmod 10$ instead of the cycle length.",
 "source":"Original","verify":"ans = pow(7, 2027, 10)"}
```
Fields:
- `id`: `<PREFIX>-NNN` (3 digits, sequential). `section`: `Quant` | `Verbal` | `Analytical` | `Spatial`. `topic`: **exactly one** of the canonical topics in §6. `subtopic`: free short text.
- `difficulty` 1|2|3, `marks` 1|2, `type` `MCQ`|`MSQ`|`NAT`.
- `q`: the stem. HTML allowed (`<b> <i> <br> <table> <ul>`; tables: plain `<table><tr><th>…`). Math in KaTeX: `$...$` inline, `$$...$$` display. **Never use `$` for money** — use ₹ or "Rs.". Escape backslashes for JSON (`\\frac`).
- `options`: exactly 4 strings (MCQ/MSQ only, no "A." prefixes). For pure-number options write plain numbers (`"12"`, `"-4"`, `"2.5"`, `"$\\frac{3}{8}$"`, `"40%"`, `"₹ 1200"`) so the checker can match them.
- `answer`: MCQ `"C"`; MSQ `["A","C"]`; NAT `{"min": 12, "max": 12}` (use a small range only when rounding is involved, e.g. `{"min": 3.14, "max": 3.15}` and say "correct to two decimal places").
- `solution`: step-by-step but concise (3–8 short lines with `<br>`), shows the key idea/formula, and ends with `Trap:` or `Shortcut:` when useful.
- `source`: `"Original"`.
- `verify` (see §5): Python code that **independently** computes the answer and sets `ans`.
- Optional `group`: shared id (e.g. `"QN7-G05"`) for 2–4 questions on the same data set/passage; each question in the group repeats the full `q` context (chart/table/passage) so it renders alone. Keep groups ≤ 4.
- Optional `chart` (Data Interpretation): rendered by the site as an SVG with values printed on the bars/points/slices:
  `{"type":"bar|groupbar|stackbar|line|pie","title":"…","labels":["2019","2020"],"series":[{"name":"Product A","values":[120,150]}],"xLabel":"Year","yLabel":"Units (thousands)"}`. Pie: one series; values are the shares as stated (e.g. percentages summing to 100 or degrees summing to 360 — say which in `title`).
- Optional `figure`: `"img/q/<id>.svg"` and/or `option_figures`: 4 paths (Spatial/geometry). Draw with matplotlib (`tools/.venv/bin/python`), dark slate ink `#2F3A3A`, accent `#5E8B7E`, transparent/white background, no title text, ~4–6 inch wide, `savefig(..., format='svg', bbox_inches='tight')` into `site/img/q/`. Also save a PNG copy into `review/figs/` and **look at it with the Read tool** before using it. If options are figures, set `"options":["Figure A","Figure B","Figure C","Figure D"]` and `option_figures`.

## 5. The `verify` field (mandatory for Quant; mandatory for Analytical/Spatial items that can be brute-forced)
- Executed with `exec` in a fresh namespace (Python 3.12, stdlib + numpy + sympy; 20 s limit). It must set a variable `ans`.
- Compute **from the givens of the question**, preferably by brute force / enumeration / simulation (itertools, fractions, datetime, coordinate geometry) rather than by retyping the final formula. Use `fractions.Fraction` for exact values.
- MCQ: set `ans` to the numeric value (when all 4 options are plain numbers — the checker finds the unique matching option and compares with `answer`), or set `ans` to the letter (e.g. by building each option's truth value and picking the one that holds). MSQ: list of letters. NAT: number.
- Analytical puzzles (arrangements, ranking, truth-tellers, syllogisms via set models, coding, series, clocks, calendars, directions): encode the constraints and brute-force all possibilities; assert uniqueness when the question claims a unique arrangement.
- Verbal: no verify; instead the solution must state the deciding rule/meaning and why each distractor fails.

## 6. Canonical topics (use exactly these strings)
- **Quant**: Number System · Powers & Logarithms · Series & Progressions · Algebra & Functions · Percentages · Profit, Loss & Interest · Ratio, Proportion & Mixtures · Averages · Speed, Time & Distance · Time & Work · Permutations & Combinations · Probability · Statistics · Geometry · Mensuration · Data Interpretation · Numerical Estimation
- **Verbal**: Grammar · Vocabulary · Word Analogy · Reading Comprehension · Verbal Reasoning · Sentence Ordering
- **Analytical**: Logical Deduction · Syllogisms · Arrangements · Directions · Blood Relations · Coding-Decoding · Series & Patterns · Clocks & Calendars · Puzzles
- **Spatial**: Cubes & Dice · Paper Folding & Cutting · Mirror & Rotation · Counting Figures · Patterns & Projections · Transformations

## 7. Workflow (follow exactly)
1. Read the reference material for your topics (§1). Plan your subtopic quotas.
2. Write in batches of ~20: append the batch to `bank/<PREFIX>.jsonl` (a short Python script with `json.dumps(..., ensure_ascii=False)` per line is safest), then run
   `cd /Users/dilipkumar/Downloads/GATE2027/Aptitude/DailyTest && tools/.venv/bin/python -I tools/validate.py bank/<PREFIX>.jsonl`
   and fix every ERROR (and sensible WARNs) before the next batch. A verify mismatch means the question, the key or the code is wrong — find out which; never "fix" the code to match a wrong key.
3. If you are restarted and the file already exists, read it, keep valid items and continue numbering.
4. At the end: final validate must show **0 errors**; check letter balance and mix lines it prints. Then write `status/<PREFIX>.txt` with: count, topic/subtopic counts, mix, and the final line `STATUS: COMPLETE`.
5. Your final reply: 5–10 lines — counts, anything you dropped or were unsure about. Do not paste questions in the reply.
Do not edit files other than your own bank file, your figures (`site/img/q/<PREFIX>-*`, `review/figs/<PREFIX>-*`) and your status file.
