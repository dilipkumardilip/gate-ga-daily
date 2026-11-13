# Adjudication log (blind-solve disagreements and flags)

## VB2
- VB2-024 key B confirmed (solver C "rigorously … unsurprised" is illogical). KEEP.
- Flags 007, 023, 031, 050, 070, 079, 104, 108, 117, 136, 141, 144, 163, 166, 167: reviewed — one clearly best option, solution explains near-misses. KEEP.

## QN4 / QN6 (190 answered, 0 mismatches)
- QN4-047 flag: natural reading (distance along track when P finishes). KEEP.
- QN4-093 flag: "within 10 days" → "in at most 10 days" (fixes.jsonl) so option A (exactly 10 days) is unambiguously included.

## QN1 / QN3 (240 answered, 0 mismatches)
- Flags QN1-044 (answer 0 is intended trick), QN1-105, QN1-110 (closest option clearly separated), QN3-035, 062, 069, 114 (MSQ keys correct; margins deliberate): KEEP.

## VB1 (170 answered, 1 mismatch)
- VB1-168 key A confirmed ("police have"; solver chose "police has"). KEEP.
- Flags 023, 028, 048, 057, 066, 068, 072, 090, 106, 111, 148, 158, 163 + strict-rule MSQs: standard textbook rules, single best answer. KEEP.

## QN5 (120 answered, 1 mismatch)
- QN5-086 key [A,B] confirmed (P(K|R)=2/6=1/3; verify enumerates the deck). KEEP.
## QN2 (partial)
- QN2-091 key [A,D] confirmed (x²|x| is even; verify checks). KEEP.
## QN7 / QN2 rest (200 answered)
- QN7-018 key B confirmed (Sep +50% > Dec −44.4%). KEEP.
- QN7-042: option D reworded to "strictly higher … than each of the other two" (fixes.jsonl) to remove tie ambiguity; key [A,C] unchanged.

## VB3 (170 answered, 3 mismatches)
- VB3-095 key [A,D] confirmed (B strengthens). VB3-102 key D confirmed ("only if" trap). VB3-145 key B confirmed (R "however" before Q "This is why"). KEEP.
- Flags 072, 103, 136: solutions state the strict reading explicitly. KEEP.

## AN1 (170 answered, 1 mismatch)
- AN1-035 key C confirmed (either-or needs a complementary pair on the same terms). KEEP.
- Existential-import flags (002…058): GATE convention treats all named terms as non-empty; keys consistent with it. KEEP.
- 083, 097 ("unless" = if-not, strict reading, explained in solution), 158 (agreed): KEEP.

## SP1 / SP2 (100 answered, 0 mismatches)
- SP2-005: figure (III) arrow looked like it pointed down; regenerated with a right-to-left arrow (matches stem). Key 20 unchanged.
- SP2-050, 003, 007: small SVGs — site CSS now scales question SVGs to ≥340px and option SVGs to ≥200px.
- SP1-010/011/022 share the same die views → group SP1-G-DIE3 (fixes.jsonl) so they never appear on the same day.

## AN2 (170 answered, 1 mismatch)
- AN2-080 key A (Bharat faces south) confirmed; solver fell for the trap. KEEP.
- Flags 006, 010, 043, 085 (NAT with 2-dp range; GATE has a calculator), 102/109/115 (standard full-sibling reading), 158 (2-dp stated): KEEP.

## Summary
1700 originals blind-solved: 10 mismatches, all keys confirmed; 5 items edited via fixes.jsonl; 0 dropped. PYQs (287) not re-solved: official keys, previously re-derived (Notes/_tools/GA_src research) and re-checked on conversion.
