#!/usr/bin/env python3
"""Assemble 60 daily tests (30 questions each) from bank/*.jsonl -> site/data.

Day composition (GATE GA ratios, x3):  Q1-15 are 1-mark, Q16-30 are 2-mark.
            1-mark  2-mark
  Verbal       5       4
  Quant        6       7
  Analytical   3       3
  Spatial      1       1
Days 58-60 each contain the complete GA section of GATE DA 2024 / 2025 / 2026.
Difficulty ramps up over the 60 days; topics are spread so that no day is lopsided.

Inputs : bank/*.jsonl, review/drop.txt (ids to exclude, one per line, '#' comments),
         review/fixes.jsonl (corrected items; replace bank items with the same id)
Output : site/data/manifest.js, site/data/days/dayNN.js, review/assembly_report.md
"""
import json, os, glob, random, math, collections, datetime, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NDAYS = 60
SECS = ['Verbal', 'Quant', 'Analytical', 'Spatial']
COMP = {('Verbal', 1): 5, ('Quant', 1): 6, ('Analytical', 1): 3, ('Spatial', 1): 1,
        ('Verbal', 2): 4, ('Quant', 2): 7, ('Analytical', 2): 3, ('Spatial', 2): 1}
CAP = {'Verbal': 3, 'Quant': 2, 'Analytical': 2, 'Spatial': 1}   # max same-topic questions per day per section
FORCED = {58: 'PYQ-DA2024-', 59: 'PYQ-DA2025-', 60: 'PYQ-DA2026-'}
PROTECT = {'Data Interpretation'}
KEEP = ['id', 'section', 'topic', 'subtopic', 'difficulty', 'marks', 'type', 'q', 'options', 'option_figures', 'figure', 'chart',
        'answer', 'solution', 'source', 'pyq', 'group']
rng = random.Random(2027)
MATH = re.compile(r'\$\$(.+?)\$\$|\$(.+?)\$', re.S)


def mathsafe(s):
    def f(m):
        dd = m.group(1) is not None
        body = (m.group(1) if dd else m.group(2)).replace('<', '\\lt ').replace('>', '\\gt ')
        return ('$$%s$$' if dd else '$%s$') % body
    return MATH.sub(f, s)


def load_bank():
    items = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'bank', '*.jsonl'))):
        for line in open(f, encoding='utf-8'):
            if line.strip():
                q = json.loads(line); items[q['id']] = q
    fx = os.path.join(ROOT, 'review', 'fixes.jsonl')
    if os.path.exists(fx):
        for line in open(fx, encoding='utf-8'):
            if line.strip():
                q = json.loads(line)
                if q['id'] in items: items[q['id']] = q
    drop = set()
    dp = os.path.join(ROOT, 'review', 'drop.txt')
    if os.path.exists(dp):
        for line in open(dp, encoding='utf-8'):
            t = line.split('#')[0].strip()
            if t: drop.add(t)
    for k in drop: items.pop(k, None)
    for q in items.values():
        q['pyq'] = bool(q.get('pyq') or q['id'].startswith('PYQ-'))
    return items, drop


def main():
    items, drop = load_bank()
    pools = collections.defaultdict(list)
    forced = collections.defaultdict(list)
    for q in items.values():
        hit = [d for d, p in FORCED.items() if q['id'].startswith(p)]
        if hit: forced[hit[0]].append(q)
        else: pools[(q['section'], q['marks'])].append(q)
    for d in forced: forced[d].sort(key=lambda q: int(re.sub(r'\D', '', q['id'].split('-Q')[-1]) or 0))

    # per-day composition
    comp = {d: dict(COMP) for d in range(1, NDAYS + 1)}
    for d, fq in forced.items():
        c = collections.Counter((q['section'], q['marks']) for q in fq)
        for m in (1, 2):
            want = {s: COMP[(s, m)] for s in SECS}
            need_total = 15
            new = {s: c[(s, m)] for s in SECS}
            left = need_total - sum(new.values())
            # fill the remaining slots proportionally to the default composition minus what is forced
            while left > 0:
                s = max(SECS, key=lambda s: (want[s] - new[s], s == 'Quant'))
                new[s] += 1; left -= 1
            for s in SECS: comp[d][(s, m)] = new[s]
    # pool needs (excluding forced) and feasibility repair
    def needs():
        n = collections.Counter()
        for d in comp:
            fc = collections.Counter((q['section'], q['marks']) for q in forced.get(d, []))
            for k, v in comp[d].items(): n[k] += v - fc[k]
        return n
    log = []
    for _ in range(400):
        n = needs()
        deficit = [k for k in n if n[k] > len(pools[k])]
        if not deficit: break
        k = deficit[0]
        # first try re-marking a difficulty-2 item of the same section from the other marks pool
        other = (k[0], 3 - k[1])
        if len(pools[other]) > n[other]:
            cand = [q for q in pools[other] if q['difficulty'] == 2 and not q['pyq']] or [q for q in pools[other] if not q['pyq']]
            if cand:
                q = rng.choice(cand); pools[other].remove(q); q['marks'] = k[1]; pools[k].append(q)
                log.append(f'remarked {q["id"]} {other} -> {k}'); continue
        # else move one slot on some non-forced day to the same-marks section with the largest surplus
        surplus = max((s for s in SECS if s != k[0]), key=lambda s: len(pools[(s, k[1])]) - n[(s, k[1])])
        if len(pools[(surplus, k[1])]) - n[(surplus, k[1])] <= 0:
            sys.exit(f'cannot fill pool {k}: need {n[k]}, have {len(pools[k])}')
        for d in sorted(comp, key=lambda d: -d):
            if d not in forced and comp[d][k] > 0:
                comp[d][k] -= 1; comp[d][(surplus, k[1])] += 1
                log.append(f'day {d}: one {k} slot -> {(surplus, k[1])}'); break
    n = needs()

    # trim surplus: random originals, never PYQs
    for k, lst in pools.items():
        extra = len(lst) - n[k]
        if extra > 0:
            orig = [q for q in lst if not q['pyq']]
            rng.shuffle(orig)
            # random (proportional) trimming; high-frequency GATE topics are trimmed last
            orig.sort(key=lambda q: q['topic'] in PROTECT)
            for q in orig[:extra]:
                lst.remove(q); log.append(f'surplus (unused): {q["id"]}')

    # allocate: sort by difficulty + noise, chunk into days in order (ramp)
    days = {d: list(forced.get(d, [])) for d in range(1, NDAYS + 1)}
    alloc = {}
    for k, lst in pools.items():
        for q in lst: q['_key'] = q['difficulty'] + rng.uniform(-1.05, 1.05)
        lst.sort(key=lambda q: q['_key'])
        i = 0
        for d in range(1, NDAYS + 1):
            fc = sum(1 for q in forced.get(d, []) if (q['section'], q['marks']) == k)
            c = comp[d][k] - fc
            alloc[(k, d)] = lst[i:i + c]; i += c

    def conflicts(k, d, lst):
        sec = k[0]
        allq = alloc.get(((sec, 1), d), []) + alloc.get(((sec, 2), d), []) + [q for q in forced.get(d, []) if q['section'] == sec]
        tc = collections.Counter(q['topic'] for q in allq)
        gc = collections.Counter(q.get('group') for q in allq if q.get('group'))
        sc = collections.Counter((q['topic'], q.get('subtopic', '').lower()) for q in allq)
        return sum(max(0, v - CAP[sec]) for v in tc.values()) * 2 + sum(v - 1 for v in gc.values()) * 3 + sum(v - 1 for v in sc.values())

    # repair: swap within the same pool between nearby days to cut topic/group clashes
    for rnd in range(6):
        changed = 0
        for k in pools:
            for d in range(1, NDAYS + 1):
                if conflicts(k, d, None) == 0: continue
                for off in (1, -1, 2, -2, 3, -3, 4, -4, 5, -5, 6, -6):
                    e = d + off
                    if not (1 <= e <= NDAYS) or not alloc.get((k, e)): continue
                    before = conflicts(k, d, None) + conflicts(k, e, None)
                    best = None
                    for i, a in enumerate(alloc[(k, d)]):
                        for j, b in enumerate(alloc[(k, e)]):
                            alloc[(k, d)][i], alloc[(k, e)][j] = b, a
                            after = conflicts(k, d, None) + conflicts(k, e, None)
                            alloc[(k, d)][i], alloc[(k, e)][j] = a, b
                            if after < before and (best is None or after < best[0]): best = (after, i, j)
                    if best:
                        _, i, j = best
                        alloc[(k, d)][i], alloc[(k, e)][j] = alloc[(k, e)][j], alloc[(k, d)][i]
                        changed += 1
                    if conflicts(k, d, None) == 0: break
        if not changed: break

    # balance PYQs across days: swap a PYQ from a PYQ-heavy day with a same-pool original of similar difficulty on a light day
    def npyq(d): return sum(q['pyq'] for k in pools for q in alloc.get((k, d), []))
    free = [d for d in range(1, NDAYS + 1) if d not in FORCED]
    for _ in range(2000):
        hi = max(free, key=npyq); lo = min(free, key=npyq)
        if npyq(hi) - npyq(lo) <= 1: break
        done = False
        for k in pools:
            for i, a in enumerate(alloc.get((k, hi), [])):
                if not a['pyq']: continue
                for j, b in enumerate(alloc.get((k, lo), [])):
                    if b['pyq'] or abs(a['difficulty'] - b['difficulty']) > 1: continue
                    before = conflicts(k, hi, None) + conflicts(k, lo, None)
                    alloc[(k, hi)][i], alloc[(k, lo)][j] = b, a
                    if conflicts(k, hi, None) + conflicts(k, lo, None) <= before: done = True; break
                    alloc[(k, hi)][i], alloc[(k, lo)][j] = a, b
                if done: break
            if done: break
        if not done: free.remove(hi if npyq(hi) > 4 else lo)
        if len(free) < 2: break

    # build day files
    os.makedirs(os.path.join(ROOT, 'site', 'data', 'days'), exist_ok=True)
    manifest = {'version': int(datetime.datetime.now().strftime('%Y%m%d%H%M')), 'generated': datetime.date.today().isoformat(), 'days': []}
    total = pyq = 0
    report = ['# Assembly report', '', '| Day | Verbal | Quant | Analytical | Spatial | PYQ | mean diff | clashes |', '|---|---|---|---|---|---|---|---|']
    used = set()
    for d in range(1, NDAYS + 1):
        qs = []
        for m in (1, 2):
            for s in SECS:
                part = [q for q in forced.get(d, []) if (q['section'], q['marks']) == (s, m)] + alloc.get(((s, m), d), [])
                part.sort(key=lambda q: (q['topic'], q['id']))
                qs += part
        assert len(qs) == 30, (d, len(qs))
        assert sum(q['marks'] for q in qs) == 45, d
        for q in qs:
            assert q['id'] not in used, q['id']; used.add(q['id'])
        out = [{k: q[k] for k in KEEP if k in q and q[k] not in (None, '', [])} for q in qs]
        for o in out:   # '<' inside $..$ would be parsed as an HTML tag by innerHTML -> use \lt / \gt
            for k in ('q', 'solution'):
                if k in o: o[k] = mathsafe(o[k])
            if 'options' in o: o['options'] = [mathsafe(str(x)) for x in o['options']]
        for o, q in zip(out, qs): o['pyq'] = q['pyq']
        cnt = collections.Counter(q['section'] for q in qs)
        tc = collections.Counter(q['topic'] for q in qs)
        focus = [t for t, _ in tc.most_common(5)]
        p = sum(q['pyq'] for q in qs)
        md = sum(q['difficulty'] for q in qs) / 30
        stage = 'Foundation' if d <= 15 else 'GATE standard' if d <= 35 else 'Advanced' if d <= 57 else 'Real GATE DA paper'
        title = f'{stage} · ' + (f'includes the full GATE DA {2024 + d - 58} GA section (Q1–10 equivalent)' if d in FORCED else 'mixed GA set, all four sections')
        manifest['days'].append({'day': d, 'title': title, 'focus': focus, 'counts': {s: cnt[s] for s in SECS}, 'pyq': p, 'difficulty': round(md, 2)})
        total += 30; pyq += p
        js = '(window.GA_DAYS = window.GA_DAYS || {})[%d] = %s;\n' % (d, json.dumps({'day': d, 'questions': out}, ensure_ascii=False, separators=(',', ':')))
        open(os.path.join(ROOT, 'site', 'data', 'days', f'day{d:02d}.js'), 'w', encoding='utf-8').write(js)
        clash = sum(conflicts(((s, m)), d, None) for s in SECS for m in (1, 2) if ((s, m), d) in alloc) // 2
        report.append(f'| {d} | {cnt["Verbal"]} | {cnt["Quant"]} | {cnt["Analytical"]} | {cnt["Spatial"]} | {p} | {md:.2f} | {clash} |')
    manifest['total'] = total; manifest['pyq'] = pyq
    open(os.path.join(ROOT, 'site', 'data', 'manifest.js'), 'w', encoding='utf-8').write('window.GA_MANIFEST = ' + json.dumps(manifest, ensure_ascii=False, indent=1) + ';\n')
    # topic coverage
    tcount = collections.Counter((q['section'], q['topic']) for q in items.values() if q['id'] in used)
    report += ['', '## Topic coverage (questions used)', ''] + [f'- {s} · {t}: {c}' for (s, t), c in sorted(tcount.items())]
    report += ['', f'Unused bank items: {len(items) - len(used)} · dropped by review: {len(drop)}', '', '## Log', ''] + [f'- {x}' for x in log]
    os.makedirs(os.path.join(ROOT, 'review'), exist_ok=True)
    open(os.path.join(ROOT, 'review', 'assembly_report.md'), 'w').write('\n'.join(report) + '\n')
    print(f'{total} questions in {NDAYS} days, {pyq} PYQs, {len(items) - len(used)} unused; report: review/assembly_report.md')


if __name__ == '__main__':
    main()
