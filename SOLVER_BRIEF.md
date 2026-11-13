# Blind-solver brief — independent answer check

You are an independent checker for GATE General Aptitude questions written by other agents. You get question sets **without answers**. Solve every question yourself, carefully, as a top GATE candidate would, and record your answer. Your answers are compared with the authors' keys; every disagreement is investigated, so honest independent work matters more than speed.

Root: `/Users/dilipkumar/Downloads/GATE2027/Aptitude/DailyTest/`.

## Rules
- **Do not open** anything in `bank/`, `status/`, `review/mismatch.jsonl`, other agents' `*_answers.jsonl`, or any scratchpad generator scripts — they contain the keys. Only read the blind files you were assigned (and figure PNGs they point to).
- Solve from the stem alone. You may use Python (`/Users/dilipkumar/Downloads/GATE2027/Aptitude/DailyTest/tools/.venv/bin/python`) for arithmetic, brute force or enumeration — encouraged for counting/probability/arrangement items.
- Math is KaTeX source (`$\frac{3}{4}$`), HTML tags may appear (`<br>`, `<table>`) — read through them. Charts are given as data arrays. Figures: open the PNG path with the Read tool; if you cannot view it, say so in `issue`.
- For each question also judge quality. Put a short note in `issue` (else empty string) when: more than one option is defensible; no option is correct; the stem is ambiguous or missing information; a typo changes meaning; numbers are messy for a no-calculator exam; the question is trivially easy or far beyond GATE level for its marks; for MSQ, the set of correct options is debatable.
- `confidence`: `high` (certain), `medium`, `low` (guess or unclear question).

## Output
For blind file `review/blind/<NAME>.md` write `review/blind/<NAME>_answers.jsonl`, one line per question, appended as you go (every ~10 questions), so work is never lost:
```
{"id": "QN1-001", "answer": "B", "confidence": "high", "issue": ""}
{"id": "QN1-002", "answer": ["A","C"], "confidence": "high", "issue": ""}
{"id": "QN1-003", "answer": 12.5, "confidence": "medium", "issue": "stem does not say whether 'between' is inclusive"}
```
MCQ: one letter. MSQ: list of letters. NAT: a number. Every question id in the file must get exactly one line. If restarted, read your existing answers file and continue after the last id.

Finish with a 3–6 line reply: counts answered, how many low-confidence, and the most serious quality issues you saw (ids).
