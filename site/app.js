/* GA Daily — 60-day GATE General Aptitude test series. Pure static site; progress in localStorage. */
(function () {
  'use strict';
  const M = window.GA_MANIFEST || { days: [] };
  const NDAYS = M.days.length;
  const KEY = 'gaDaily.v1';
  const L = 'ABCD';
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const app = $('#app');
  const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const pad = n => String(n).padStart(2, '0');
  const fmtTime = s => { s = Math.max(0, Math.round(s)); const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), x = s % 60; return (h ? h + ':' + pad(m) : m) + ':' + pad(x); };
  const fmtMarks = v => (Math.round(v * 100) / 100).toString();
  const todayISO = () => { const d = new Date(); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; };

  /* ---------- state ---------- */
  let S = load();
  function load() {
    let s = null;
    try { s = JSON.parse(localStorage.getItem(KEY)); } catch (e) { s = null; }
    s = s || {};
    s.settings = Object.assign({ startDate: todayISO(), duration: 60, showTopic: false }, s.settings || {});
    s.days = s.days || {};
    s.cleared = s.cleared || {};
    s.notes = s.notes || {};
    return s;
  }
  let saveTimer = null;
  function save(now) {
    clearTimeout(saveTimer);
    const w = () => { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { console.warn('save failed', e); } };
    if (now) w(); else saveTimer = setTimeout(w, 250);
  }
  window.addEventListener('beforeunload', () => save(true));

  const todayDay = () => {
    const a = new Date(S.settings.startDate + 'T00:00:00'), b = new Date(todayISO() + 'T00:00:00');
    return Math.min(NDAYS, Math.max(1, Math.floor((b - a) / 864e5) + 1));
  };
  const dayMeta = n => M.days[n - 1];

  /* ---------- data loading (script tags work on file:// and GitHub Pages) ---------- */
  window.GA_DAYS = window.GA_DAYS || {};
  const loading = {};
  function loadDay(n) {
    if (window.GA_DAYS[n]) return Promise.resolve(window.GA_DAYS[n]);
    if (loading[n]) return loading[n];
    loading[n] = new Promise((res, rej) => {
      const s = document.createElement('script');
      s.src = `data/days/day${pad(n)}.js?v=${M.version || 1}`;
      s.onload = () => (window.GA_DAYS[n] ? res(window.GA_DAYS[n]) : rej(new Error('day file empty')));
      s.onerror = () => { delete loading[n]; rej(new Error('Could not load day ' + n)); };
      document.head.appendChild(s);
    });
    return loading[n];
  }

  /* ---------- helpers ---------- */
  function math(el) {
    if (window.renderMathInElement) {
      try {
        renderMathInElement(el, { delimiters: [{ left: '$$', right: '$$', display: true }, { left: '$', right: '$', display: false }], throwOnError: false, ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code', 'option'] });
      } catch (e) { /* ignore */ }
    }
  }
  function evaluate(q, r) {
    const neg = q.type === 'MCQ' ? q.marks / 3 : 0;
    if (r === undefined || r === null || r === '' || (Array.isArray(r) && !r.length)) return { st: 'skipped', m: 0 };
    let ok = false;
    if (q.type === 'MCQ') ok = r === q.answer;
    else if (q.type === 'MSQ') ok = [...r].sort().join() === [...q.answer].sort().join();
    else if (q.type === 'NAT') { const v = parseFloat(String(r).replace(/,/g, '')); ok = !isNaN(v) && v >= q.answer.min - 1e-9 && v <= q.answer.max + 1e-9; }
    return ok ? { st: 'correct', m: q.marks } : { st: 'wrong', m: -neg };
  }
  const ansText = q => q.type === 'MCQ' ? q.answer : q.type === 'MSQ' ? q.answer.join(', ') :
    (q.answer.min === q.answer.max ? String(q.answer.min) : `${q.answer.min} to ${q.answer.max}`);
  const respText = (q, r) => (r === undefined || r === '' || r === null || (Array.isArray(r) && !r.length)) ? '—' : Array.isArray(r) ? [...r].sort().join(', ') : String(r);
  const typeChip = q => q.type === 'MCQ' ? '<span class="chip">MCQ</span>' : q.type === 'MSQ' ? '<span class="chip blue">MSQ · one or more correct</span>' : '<span class="chip blue">NAT · numerical</span>';
  const marksChip = q => `<span class="chip ${q.marks === 2 ? 'm2' : ''}">${q.marks} mark${q.marks > 1 ? 's' : ''}</span>`;

  function qBody(q) {
    let h = `<div class="qtext">${q.q}</div>`;
    if (q.chart && window.GACharts) h += `<div class="chart">${GACharts.render(q.chart)}</div>`;
    if (q.figure) h += `<div class="qfig"><img src="${esc(q.figure)}" alt="Figure for the question"></div>`;
    return h;
  }
  function optInner(q, i) {
    const f = q.option_figures && q.option_figures[i];
    return f ? `<img src="${esc(f)}" alt="Option ${L[i]}">` : q.options[i];
  }

  /* ---------- router ---------- */
  let cleanup = null;
  function route() {
    if (cleanup) { cleanup(); cleanup = null; }
    document.body.classList.remove('testing');
    closeCalc();
    const h = location.hash.replace(/^#\/?/, '');
    const [page, arg] = h.split('/');
    $$('.nav a').forEach(a => a.classList.toggle('active', a.dataset.nav === (page || 'home') || (!page && a.dataset.nav === 'home')));
    window.scrollTo(0, 0);
    if (!NDAYS) { app.innerHTML = '<div class="card empty">Question data not found. Make sure <code>data/manifest.js</code> exists.</div>'; return; }
    const n = Math.min(NDAYS, Math.max(1, parseInt(arg, 10) || 1));
    if (page === 'day') return viewIntro(n);
    if (page === 'test') return viewTest(n);
    if (page === 'result') return viewResult(n);
    if (page === 'progress') return viewProgress();
    if (page === 'mistakes') return viewMistakes();
    if (page === 'settings') return viewSettings();
    return viewHome();
  }
  window.addEventListener('hashchange', route);

  /* ---------- home ---------- */
  function dayStatus(n) {
    const d = S.days[n];
    if (!d) return { cls: '', txt: 'Not started' };
    if (d.result) return { cls: 'done', txt: `${fmtMarks(d.result.score)} / ${d.result.max}` };
    return { cls: 'progress', txt: `In progress · ${Object.keys(d.answers || {}).length}/30` };
  }
  function viewHome() {
    const t = todayDay(), tm = dayMeta(t), ts = S.days[t];
    const done = Object.values(S.days).filter(d => d.result);
    const avg = done.length ? done.reduce((a, d) => a + d.result.score / d.result.max, 0) / done.length * 100 : 0;
    const streak = calcStreak();
    const btn = ts && ts.result ? `<a class="btn" href="#/result/${t}">View result</a><a class="btn soft" href="#/day/${t}">Retake</a>`
      : ts ? `<a class="btn primary" href="#/test/${t}">Resume test →</a>` : `<a class="btn primary" href="#/day/${t}">Start today's test →</a>`;
    let html = `<section class="hero">
      <div class="card today">
        <div class="eyebrow">Today · ${new Date().toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' })}</div>
        <h1>Day ${t} of ${NDAYS}</h1>
        <div class="muted">${esc(tm.title || '')}</div>
        <div class="focus-list">${(tm.focus || []).map(f => `<span class="chip">${esc(f)}</span>`).join('')}</div>
        <div class="row">${btn}</div>
      </div>
      <div class="card">
        <h3>Your run</h3>
        <div class="grid-stats" style="margin-top:.6rem">
          <div class="stat"><b class="num">${done.length}<small class="muted" style="font-size:.9rem">/${NDAYS}</small></b><span>days completed</span></div>
          <div class="stat"><b class="num">${done.length ? avg.toFixed(0) + '%' : '—'}</b><span>average score</span></div>
          <div class="stat"><b class="num">${streak}</b><span>day streak</span></div>
        </div>
        <p class="small muted" style="margin:.9rem 0 0">Each day: 30 questions · 45 marks · ${S.settings.duration} min. 15 one-mark + 15 two-mark, GATE negative marking for MCQs.</p>
      </div>
    </section>
    <div class="section-title"><h2>All 60 days</h2><span class="small muted">Started ${new Date(S.settings.startDate + 'T00:00:00').toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })} · <a href="#/settings">change</a></span></div>
    <div class="days">`;
    for (let n = 1; n <= NDAYS; n++) {
      if ((n - 1) % 7 === 0) html += `<div class="week-label">Week ${Math.floor((n - 1) / 7) + 1}</div>`;
      const m = dayMeta(n), st = dayStatus(n);
      const href = S.days[n] && S.days[n].result ? `#/result/${n}` : S.days[n] ? `#/test/${n}` : `#/day/${n}`;
      html += `<a class="day ${st.cls} ${n === t ? 'today' : ''} ${n > t && !S.days[n] ? 'future' : ''}" href="${href}">
        ${n === t ? '<span class="tag">TODAY</span>' : ''}
        <span class="dn">Day ${n}</span><span class="df">${esc((m.focus || []).join(' · '))}</span><span class="ds">${st.txt}</span></a>`;
    }
    app.innerHTML = html + '</div>';
  }
  function calcStreak() {
    const dates = new Set(Object.values(S.days).filter(d => d.result && d.submittedAt).map(d => d.submittedAt.slice(0, 10)));
    let c = 0, d = new Date();
    const iso = x => `${x.getFullYear()}-${pad(x.getMonth() + 1)}-${pad(x.getDate())}`;
    if (!dates.has(iso(d))) d.setDate(d.getDate() - 1);
    while (dates.has(iso(d))) { c++; d.setDate(d.getDate() - 1); }
    return c;
  }

  /* ---------- intro ---------- */
  function viewIntro(n) {
    const m = dayMeta(n), d = S.days[n];
    const c = m.counts || {};
    app.innerHTML = `<div class="intro card">
      <div class="small muted"><a href="#/">← All days</a></div>
      <h1 style="margin-top:.6rem">Day ${n}</h1>
      <p class="muted" style="margin-top:-.2rem">${esc(m.title || '')}</p>
      <div class="focus-list">${(m.focus || []).map(f => `<span class="chip">${esc(f)}</span>`).join('')}</div>
      <div class="mixgrid">
        <div><b>${c.Verbal || 0}</b><span>Verbal</span></div><div><b>${c.Quant || 0}</b><span>Quantitative</span></div>
        <div><b>${c.Analytical || 0}</b><span>Analytical</span></div><div><b>${c.Spatial || 0}</b><span>Spatial</span></div>
      </div>
      <ul class="small">
        <li><b>30 questions, 45 marks, ${S.settings.duration} minutes.</b> Q1–15 carry 1 mark, Q16–30 carry 2 marks (like GATE's Q1–5 / Q6–10).</li>
        <li>MCQ wrong answer: −1/3 (1-mark) or −2/3 (2-mark). MSQ and NAT: no negative marks; MSQ needs the exact set.</li>
        <li>Your answers save automatically in this browser — you can close the tab and resume. The timer runs only while the test is open.</li>
        <li>A basic calculator is available (like GATE's virtual calculator). Keys: <b>1–4 / A–D</b> select, <b>←/→</b> previous/next, <b>M</b> mark for review.</li>
        ${m.pyq ? `<li>${m.pyq} of today's questions are real GATE previous-year questions; the source is shown after you submit.</li>` : ''}
      </ul>
      <div class="row" style="margin-top:1.2rem">
        ${d && d.result ? `<a class="btn" href="#/result/${n}">View last result</a><button class="btn primary" id="retake">Retake Day ${n}</button>`
        : d ? `<a class="btn primary" href="#/test/${n}">Resume →</a>` : `<a class="btn primary" href="#/test/${n}">Start test →</a>`}
      </div></div>`;
    const r = $('#retake');
    if (r) r.onclick = () => {
      confirmBox('Retake this day?', 'Your previous score stays in history; the attempt starts fresh.', 'Retake', () => {
        const old = S.days[n];
        S.days[n] = { history: [...(old.history || []), { result: old.result, submittedAt: old.submittedAt }] };
        save(true); location.hash = `#/test/${n}`;
      });
    };
  }

  /* ---------- test ---------- */
  function viewTest(n) {
    app.innerHTML = '<p class="loading">Loading Day ' + n + '…</p>';
    loadDay(n).then(D => startTest(n, D)).catch(e => (app.innerHTML = `<div class="card empty">${esc(e.message)}</div>`));
  }
  function startTest(n, D) {
    const qs = D.questions;
    let d = S.days[n];
    if (d && d.result) { location.hash = `#/result/${n}`; return; }
    if (!d || !d.answers) {
      d = S.days[n] = Object.assign(S.days[n] || {}, { startedAt: new Date().toISOString(), elapsed: 0, cur: 0, answers: {}, marked: {}, visited: {}, qtime: {} });
    }
    const limit = S.settings.duration * 60;
    document.body.classList.add('testing');
    app.innerHTML = `<div class="test">
      <div><div class="card qcard" id="qcard"></div></div>
      <aside class="side">
        <div class="card timer" id="timerCard"><div><div class="small muted">Time left</div><b id="timer">--:--</b></div>
          <button class="btn soft" id="calcBtn" title="Calculator">Calculator</button></div>
        <div class="card">
          <div class="row" style="justify-content:space-between;margin-bottom:.6rem"><b>Day ${n}</b><span class="small muted" id="answeredCount"></span></div>
          <div class="small muted" style="margin-bottom:.35rem">Q1–15 · 1 mark</div>
          <div class="palette" id="pal1"></div>
          <div class="small muted" style="margin:.7rem 0 .35rem">Q16–30 · 2 marks</div>
          <div class="palette" id="pal2"></div>
          <div class="legend"><span><i style="background:#fff"></i>Not visited</span><span><i style="background:var(--wrong-bg)"></i>Not answered</span>
            <span><i style="background:var(--accent)"></i>Answered</span><span><i style="background:var(--accent-2-bg);border-radius:50%"></i>Marked</span></div>
          <button class="btn primary" id="submitBtn" style="width:100%;margin-top:1rem">Submit test</button>
          <a class="btn" href="#/" style="width:100%;margin-top:.5rem">Save &amp; exit</a>
        </div>
      </aside></div>`;
    $('#calcBtn').onclick = toggleCalc;
    $('#submitBtn').onclick = () => {
      const a = qs.filter(q => hasResp(d.answers[q.id])).length;
      const mk = qs.filter(q => d.marked[q.id]).length;
      confirmBox('Submit Day ' + n + '?', `Answered ${a} of ${qs.length}. ${mk ? mk + ' marked for review. ' : ''}${qs.length - a ? (qs.length - a) + ' unanswered.' : ''}`, 'Submit', () => submit(n, D));
    };

    function hasResp(r) { return !(r === undefined || r === null || r === '' || (Array.isArray(r) && !r.length)); }
    function palette() {
      ['pal1', 'pal2'].forEach((id, k) => {
        $('#' + id).innerHTML = qs.slice(k * 15, k * 15 + 15).map((q, j) => {
          const i = k * 15 + j, cls = [hasResp(d.answers[q.id]) ? 'answered' : d.visited[q.id] ? 'visited' : '', d.marked[q.id] ? 'marked' : '', i === d.cur ? 'cur' : ''].join(' ');
          return `<button class="pal ${cls}" data-i="${i}" aria-label="Question ${i + 1}">${i + 1}</button>`;
        }).join('');
      });
      $$('.pal').forEach(b => (b.onclick = () => go(+b.dataset.i)));
      $('#answeredCount').textContent = `${qs.filter(q => hasResp(d.answers[q.id])).length}/30 answered`;
    }
    function render() {
      const q = qs[d.cur]; d.visited[q.id] = true;
      const r = d.answers[q.id];
      let opts = '';
      if (q.type === 'NAT') {
        opts = `<div class="nat"><input id="natIn" inputmode="decimal" autocomplete="off" placeholder="Type your answer" value="${esc(r ?? '')}"><span class="small muted">Numerical answer</span></div>`;
      } else {
        const fig = q.option_figures ? ' figs' : '';
        opts = `<div class="opts${fig}">` + q.options.map((o, i) => {
          const sel = q.type === 'MSQ' ? (r || []).includes(L[i]) : r === L[i];
          return `<button class="opt ${q.type === 'MSQ' ? 'msq' : ''} ${sel ? 'sel' : ''}" data-l="${L[i]}"><span class="ol">${L[i]}</span><span class="ot">${optInner(q, i)}</span></button>`;
        }).join('') + '</div>' + (q.type === 'MSQ' ? '<div class="hint">Select all correct options. No negative marking.</div>' : '');
      }
      $('#qcard').innerHTML = `<div class="qhead"><span class="qno">Q${d.cur + 1}</span>${marksChip(q)}${typeChip(q)}<span class="chip">${esc(q.section)}${S.settings.showTopic ? ' · ' + esc(q.topic) : ''}</span></div>
        ${qBody(q)}${opts}
        <div class="qactions"><div class="row">
          <button class="btn" id="prev" ${d.cur === 0 ? 'disabled' : ''}>← Prev</button>
          <button class="btn soft" id="clear">Clear</button>
          <button class="btn blue" id="mark">${d.marked[q.id] ? 'Unmark' : 'Mark for review'}</button></div>
          <button class="btn primary" id="next">${d.cur === qs.length - 1 ? 'Save' : 'Save &amp; next →'}</button></div>`;
      math($('#qcard'));
      $$('.opt', $('#qcard')).forEach(b => (b.onclick = () => pick(b.dataset.l)));
      const ni = $('#natIn');
      if (ni) { ni.oninput = () => { d.answers[q.id] = ni.value.trim(); if (!d.answers[q.id]) delete d.answers[q.id]; save(); palette(); }; }
      $('#prev').onclick = () => go(d.cur - 1);
      $('#next').onclick = () => go(Math.min(qs.length - 1, d.cur + 1));
      $('#clear').onclick = () => { delete d.answers[q.id]; save(); render(); };
      $('#mark').onclick = () => { d.marked[q.id] = !d.marked[q.id]; if (!d.marked[q.id]) delete d.marked[q.id]; save(); if (d.marked[q.id] && d.cur < qs.length - 1) go(d.cur + 1); else render(); };
      palette();
    }
    function pick(l) {
      const q = qs[d.cur];
      if (q.type === 'MSQ') {
        const cur = new Set(d.answers[q.id] || []); cur.has(l) ? cur.delete(l) : cur.add(l);
        d.answers[q.id] = [...cur].sort(); if (!cur.size) delete d.answers[q.id];
      } else d.answers[q.id] = d.answers[q.id] === l ? undefined : l;
      if (d.answers[q.id] === undefined) delete d.answers[q.id];
      save(); render();
    }
    function go(i) { if (i < 0 || i >= qs.length) return; d.cur = i; save(); render(); window.scrollTo({ top: 0, behavior: 'smooth' }); }
    function tick() {
      if (document.hidden) return;
      d.elapsed = (d.elapsed || 0) + 1;
      const q = qs[d.cur]; d.qtime[q.id] = (d.qtime[q.id] || 0) + 1;
      const left = limit - d.elapsed;
      $('#timer').textContent = fmtTime(left);
      $('#timerCard').classList.toggle('low', left <= 300);
      if (d.elapsed % 5 === 0) save();
      if (left <= 0) { clearInterval(iv); submit(n, D, true); }
    }
    function key(e) {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || !$('#modal').hidden) return;
      const k = e.key.toUpperCase(), q = qs[d.cur];
      if (q.type !== 'NAT' && ('1234'.includes(k) || 'ABCD'.includes(k)) && k.length === 1) { pick('ABCD'['1234'.includes(k) ? +k - 1 : 'ABCD'.indexOf(k)]); }
      else if (e.key === 'ArrowRight') go(d.cur + 1);
      else if (e.key === 'ArrowLeft') go(d.cur - 1);
      else if (k === 'M') $('#mark').click();
    }
    $('#timer').textContent = fmtTime(limit - (d.elapsed || 0));
    const iv = setInterval(tick, 1000);
    document.addEventListener('keydown', key);
    cleanup = () => { clearInterval(iv); document.removeEventListener('keydown', key); save(true); };
    render();
  }

  function submit(n, D, auto) {
    const d = S.days[n], qs = D.questions;
    const items = qs.map(q => {
      const r = d.answers[q.id], ev = evaluate(q, r);
      return { id: q.id, section: q.section, topic: q.topic, marks: q.marks, type: q.type, st: ev.st, m: ev.m, t: d.qtime[q.id] || 0, r: r ?? null };
    });
    const agg = key => {
      const o = {};
      items.forEach(it => {
        const k = it[key]; o[k] = o[k] || { n: 0, correct: 0, wrong: 0, skipped: 0, score: 0, max: 0 };
        o[k].n++; o[k][it.st]++; o[k].score += it.m; o[k].max += it.marks;
      });
      return o;
    };
    d.result = {
      score: items.reduce((a, it) => a + it.m, 0), max: items.reduce((a, it) => a + it.marks, 0),
      correct: items.filter(i => i.st === 'correct').length, wrong: items.filter(i => i.st === 'wrong').length, skipped: items.filter(i => i.st === 'skipped').length,
      negative: items.filter(i => i.m < 0).reduce((a, i) => a + i.m, 0), elapsed: d.elapsed, auto: !!auto,
      bySection: agg('section'), byTopic: agg('topic'), items
    };
    d.submittedAt = new Date().toISOString();
    save(true);
    closeModal();
    if (location.hash === `#/result/${n}`) route(); else location.hash = `#/result/${n}`;
  }

  /* ---------- result ---------- */
  function ring(p) {
    const r = 58, c = 2 * Math.PI * r, v = Math.max(0, Math.min(1, p));
    return `<svg class="ring" viewBox="0 0 140 140"><circle cx="70" cy="70" r="${r}" fill="none" stroke="#EEF2EE" stroke-width="12"/>
      <circle cx="70" cy="70" r="${r}" fill="none" stroke="#5E8B7E" stroke-width="12" stroke-linecap="round" stroke-dasharray="${c * v} ${c}" transform="rotate(-90 70 70)"/>
      <text x="70" y="76" text-anchor="middle" font-family="Fraunces, Georgia, serif" font-size="26" font-weight="600" fill="#2F3A3A">${Math.round(p * 100)}%</text></svg>`;
  }
  function viewResult(n) {
    const d = S.days[n];
    if (!d || !d.result) { location.hash = `#/day/${n}`; return; }
    app.innerHTML = '<p class="loading">Loading…</p>';
    loadDay(n).then(D => {
      const R = d.result, qs = D.questions;
      const secRows = Object.entries(R.bySection).map(([k, v]) => `<tr><td>${esc(k)}</td><td class="num">${v.n}</td><td class="num">${v.correct}</td><td class="num">${v.wrong}</td><td class="num">${v.skipped}</td><td class="num"><b>${fmtMarks(v.score)}</b> / ${v.max}</td></tr>`).join('');
      const topRows = Object.entries(R.byTopic).sort((a, b) => a[1].correct / a[1].n - b[1].correct / b[1].n).map(([k, v]) =>
        `<tr><td>${esc(k)}</td><td class="num">${v.correct}/${v.n}</td><td><div class="bar"><i style="width:${(v.correct / v.n) * 100}%"></i></div></td></tr>`).join('');
      const hist = (d.history || []).filter(h => h.result).map((h, i) => `Attempt ${i + 1}: ${fmtMarks(h.result.score)}/${h.result.max}`).join(' · ');
      app.innerHTML = `<div class="small muted"><a href="#/">← All days</a></div>
      <div class="card" style="margin-top:.8rem"><div class="score-hero">${ring(R.score / R.max)}
        <div><h1 style="margin-bottom:.2rem">Day ${n} · ${fmtMarks(R.score)} / ${R.max}</h1>
          <div class="muted small">${R.auto ? 'Auto-submitted when time ran out · ' : ''}Time used ${fmtTime(R.elapsed)} · Negative marks ${fmtMarks(R.negative)}${hist ? ' · ' + hist : ''}</div>
          <div class="grid-stats" style="margin-top:1rem">
            <div class="stat"><b class="num" style="color:var(--correct)">${R.correct}</b><span>correct</span></div>
            <div class="stat"><b class="num" style="color:var(--wrong)">${R.wrong}</b><span>wrong</span></div>
            <div class="stat"><b class="num">${R.skipped}</b><span>unattempted</span></div>
            <div class="stat"><b class="num">${R.correct + R.wrong ? Math.round(R.correct / (R.correct + R.wrong) * 100) : 0}%</b><span>accuracy</span></div>
          </div>
          <div class="row" style="margin-top:1rem"><a class="btn soft" href="#/day/${n}">Retake</a>${n < NDAYS ? `<a class="btn" href="#/day/${n + 1}">Day ${n + 1} →</a>` : ''}</div>
        </div></div></div>
      <div class="two" style="margin-top:1.2rem">
        <div class="card"><h3>By section</h3><table class="tbl"><tr><th>Section</th><th class="num">Qs</th><th class="num">✓</th><th class="num">✗</th><th class="num">–</th><th class="num">Marks</th></tr>${secRows}</table></div>
        <div class="card"><h3>By topic</h3><table class="tbl">${topRows}</table></div>
      </div>
      <div class="section-title"><h2>Review</h2><div class="filters" id="filters">
        <button data-f="all" class="on">All 30</button><button data-f="wrong">Wrong (${R.wrong})</button><button data-f="skipped">Unattempted (${R.skipped})</button><button data-f="correct">Correct (${R.correct})</button></div></div>
      <div id="reviewList"></div>`;
      const items = Object.fromEntries(R.items.map(i => [i.id, i]));
      const list = $('#reviewList');
      const draw = f => {
        list.innerHTML = qs.map((q, i) => ({ q, i, it: items[q.id] || { st: 'skipped', r: null, t: 0, m: 0 } })).filter(x => f === 'all' || x.it.st === f)
          .map(x => reviewCard(x.q, x.i, x.it)).join('') || '<div class="card empty">Nothing here.</div>';
        math(list); bindNotes(list);
      };
      $$('#filters button').forEach(b => (b.onclick = () => { $$('#filters button').forEach(x => x.classList.remove('on')); b.classList.add('on'); draw(b.dataset.f); }));
      draw('all');
    }).catch(e => (app.innerHTML = `<div class="card empty">${esc(e.message)}</div>`));
  }
  function reviewCard(q, i, it, opts = {}) {
    const verdict = { correct: `✓ Correct · +${q.marks}`, wrong: `✗ Wrong · ${fmtMarks(it.m)}`, skipped: '– Not attempted · 0' }[it.st];
    let body = '';
    if (q.type === 'NAT') {
      body = `<div class="small" style="margin-top:.8rem">Your answer: <b>${esc(respText(q, it.r))}</b> · Correct: <b>${esc(ansText(q))}</b></div>`;
    } else {
      const right = q.type === 'MSQ' ? q.answer : [q.answer];
      const mine = it.r == null ? [] : Array.isArray(it.r) ? it.r : [it.r];
      body = `<div class="opts${q.option_figures ? ' figs' : ''}">` + q.options.map((o, k) => {
        const l = L[k], cls = right.includes(l) ? 'right' : mine.includes(l) ? 'wrongsel' : '';
        return `<div class="opt ${cls}" disabled><span class="ol">${l}</span><span class="ot">${optInner(q, k)}${mine.includes(l) ? ' <span class="chip" style="margin-left:.3rem">your pick</span>' : ''}</span></div>`;
      }).join('') + '</div>';
    }
    return `<div class="card review-item ${it.st}">
      <div class="qhead"><span class="qno">${opts.label || 'Q' + (i + 1)}</span>${marksChip(q)}${typeChip(q)}<span class="chip">${esc(q.section)} · ${esc(q.topic)}</span>
        ${q.pyq ? `<span class="chip pyq">PYQ · ${esc(q.source)}</span>` : ''}<span class="grow"></span><span class="verdict ${it.st}">${verdict}</span></div>
      ${qBody(q)}${body}
      <div class="small muted" style="margin-top:.6rem">${it.t ? 'Time spent: ' + fmtTime(it.t) : ''}</div>
      <details class="sol" ${it.st !== 'correct' ? 'open' : ''}><summary>Solution · answer ${esc(ansText(q))}</summary><div class="soltext">${q.solution}</div></details>
      ${it.st !== 'correct' ? `<textarea class="note" data-id="${esc(q.id)}" placeholder="Why did I miss it? (concept gap / silly mistake / time) — saved for revision">${esc(S.notes[q.id] || '')}</textarea>` : ''}
    </div>`;
  }
  function bindNotes(el) {
    $$('textarea.note', el).forEach(t => (t.oninput = () => { if (t.value.trim()) S.notes[t.dataset.id] = t.value; else delete S.notes[t.dataset.id]; save(); }));
  }

  /* ---------- progress ---------- */
  function viewProgress() {
    const done = Object.entries(S.days).filter(([, d]) => d.result).map(([n, d]) => ({ n: +n, r: d.result })).sort((a, b) => a.n - b.n);
    if (!done.length) { app.innerHTML = '<h1>Progress</h1><div class="card empty">Finish your first day to see progress here.</div>'; return; }
    const sec = {}, top = {};
    let tot = 0, corr = 0, wr = 0, time = 0;
    done.forEach(({ r }) => r.items.forEach(it => {
      [[sec, it.section], [top, it.topic]].forEach(([o, k]) => { o[k] = o[k] || { n: 0, c: 0, w: 0, s: 0, sec: it.section }; o[k].n++; o[k][it.st[0]]++; });
      tot++; if (it.st === 'correct') corr++; if (it.st === 'wrong') wr++; time += it.t || 0;
    }));
    const W = 760, H = 230, Lp = 40, B = 28, T = 14, R = 12;
    const x = n => Lp + (W - Lp - R) * (n - 1) / Math.max(1, NDAYS - 1), y = p => T + (H - T - B) * (1 - p);
    let svg = '';
    [0, .25, .5, .75, 1].forEach(p => (svg += `<line x1="${Lp}" x2="${W - R}" y1="${y(p)}" y2="${y(p)}" stroke="#E4E9E6"/><text x="${Lp - 6}" y="${y(p) + 4}" font-size="11" fill="#6B7776" text-anchor="end">${p * 100}%</text>`));
    [1, 10, 20, 30, 40, 50, 60].filter(v => v <= NDAYS).forEach(v => (svg += `<text x="${x(v)}" y="${H - 8}" font-size="11" fill="#6B7776" text-anchor="middle">D${v}</text>`));
    svg += `<polyline fill="none" stroke="#5E8B7E" stroke-width="2.5" points="${done.map(o => `${x(o.n)},${y(Math.max(0, o.r.score / o.r.max))}`).join(' ')}"/>`;
    done.forEach(o => (svg += `<circle cx="${x(o.n)}" cy="${y(Math.max(0, o.r.score / o.r.max))}" r="4" fill="#fff" stroke="#5E8B7E" stroke-width="2"><title>Day ${o.n}: ${fmtMarks(o.r.score)}/${o.r.max}</title></circle>`));
    const secRows = Object.entries(sec).map(([k, v]) => `<tr><td>${esc(k)}</td><td class="num">${v.n}</td><td class="num">${v.c + v.w ? Math.round(v.c / (v.c + v.w) * 100) : 0}%</td><td><div class="bar"><i style="width:${v.c / v.n * 100}%"></i></div></td></tr>`).join('');
    const topRows = Object.entries(top).sort((a, b) => a[1].c / a[1].n - b[1].c / b[1].n).map(([k, v]) =>
      `<tr><td>${esc(k)}<div class="small muted">${esc(v.sec)}</div></td><td class="num">${v.c}/${v.n}</td><td class="num">${v.w}</td><td style="width:35%"><div class="bar"><i style="width:${v.c / v.n * 100}%;background:${v.c / v.n < .5 ? '#C9A24E' : '#5E8B7E'}"></i></div></td></tr>`).join('');
    app.innerHTML = `<h1>Progress</h1>
      <div class="card"><div class="grid-stats">
        <div class="stat"><b class="num">${done.length}</b><span>days done</span></div>
        <div class="stat"><b class="num">${tot}</b><span>questions seen</span></div>
        <div class="stat"><b class="num">${corr + wr ? Math.round(corr / (corr + wr) * 100) : 0}%</b><span>accuracy (attempted)</span></div>
        <div class="stat"><b class="num">${(done.reduce((a, o) => a + o.r.score / o.r.max, 0) / done.length * 100).toFixed(0)}%</b><span>average score</span></div>
        <div class="stat"><b class="num">${tot ? fmtTime(time / tot) : '—'}</b><span>avg time / question</span></div>
      </div></div>
      <div class="card" style="margin-top:1.2rem"><h3>Score by day</h3><svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto">${svg}</svg></div>
      <div class="two" style="margin-top:1.2rem">
        <div class="card"><h3>Sections</h3><table class="tbl"><tr><th>Section</th><th class="num">Qs</th><th class="num">Acc.</th><th></th></tr>${secRows}</table></div>
        <div class="card"><h3>Topics — weakest first</h3><table class="tbl"><tr><th>Topic</th><th class="num">✓</th><th class="num">✗</th><th></th></tr>${topRows}</table></div>
      </div>`;
  }

  /* ---------- mistakes (practice with instant feedback) ---------- */
  function viewMistakes() {
    const days = Object.entries(S.days).filter(([, d]) => d.result).map(([n, d]) => ({ n: +n, d }));
    const want = [];
    days.forEach(({ n, d }) => d.result.items.forEach(it => { if (it.st !== 'correct') want.push({ n, it }); }));
    if (!want.length) { app.innerHTML = '<h1>Mistakes</h1><div class="card empty">No mistakes yet. Wrong and unattempted questions from submitted days collect here for re-practice.</div>'; return; }
    app.innerHTML = '<p class="loading">Loading…</p>';
    Promise.all([...new Set(want.map(w => w.n))].map(loadDay)).then(() => {
      let showCleared = false, filter = 'all';
      const draw = () => {
        const rows = want.filter(w => (showCleared || !S.cleared[w.it.id]) && (filter === 'all' || w.it.section === filter));
        const secs = [...new Set(want.map(w => w.it.section))];
        app.innerHTML = `<h1>Mistakes</h1>
          <p class="muted" style="margin-top:-.3rem">Wrong and unattempted questions from every submitted day. Answer again — get it right and it is cleared.</p>
          <div class="row" style="margin:1rem 0"><div class="filters" id="mf"><button data-f="all" class="${filter === 'all' ? 'on' : ''}">All</button>${secs.map(s => `<button data-f="${esc(s)}" class="${filter === s ? 'on' : ''}">${esc(s)}</button>`).join('')}</div>
          <span class="grow"></span><label class="small"><input type="checkbox" id="sc" ${showCleared ? 'checked' : ''}> show cleared</label></div>
          <div id="ml">${rows.map(w => practiceCard(window.GA_DAYS[w.n].questions.find(q => q.id === w.it.id), w)).join('') || '<div class="card empty">All cleared in this filter. 🎉</div>'}</div>`;
        $$('#mf button').forEach(b => (b.onclick = () => { filter = b.dataset.f; draw(); }));
        $('#sc').onchange = e => { showCleared = e.target.checked; draw(); };
        math($('#ml')); bindPractice($('#ml'));
      };
      draw();
    });
  }
  function practiceCard(q, w) {
    if (!q) return '';
    const opts = q.type === 'NAT' ? `<div class="nat"><input class="pin" inputmode="decimal" placeholder="Your answer"><button class="btn primary pchk">Check</button></div>`
      : `<div class="opts${q.option_figures ? ' figs' : ''}">${q.options.map((o, k) => `<button class="opt ${q.type === 'MSQ' ? 'msq' : ''}" data-l="${L[k]}"><span class="ol">${L[k]}</span><span class="ot">${optInner(q, k)}</span></button>`).join('')}</div>
        ${q.type === 'MSQ' ? '<div class="row" style="margin-top:.7rem"><button class="btn primary pchk">Check</button></div>' : ''}`;
    return `<div class="card review-item ${S.cleared[q.id] ? 'correct' : 'skipped'}" data-id="${esc(q.id)}" data-day="${w.n}" style="margin-bottom:1rem">
      <div class="qhead"><span class="qno">Day ${w.n}</span>${marksChip(q)}${typeChip(q)}<span class="chip">${esc(q.section)} · ${esc(q.topic)}</span>
      ${q.pyq ? `<span class="chip pyq">PYQ · ${esc(q.source)}</span>` : ''}<span class="grow"></span><span class="small muted">${w.it.st === 'wrong' ? 'was wrong (you: ' + esc(respText(q, w.it.r)) + ')' : 'was unattempted'}</span></div>
      ${qBody(q)}${opts}<div class="pfb"></div>
      ${S.notes[q.id] ? `<div class="small muted" style="margin-top:.6rem">📝 ${esc(S.notes[q.id])}</div>` : ''}</div>`;
  }
  function bindPractice(root) {
    $$('.review-item', root).forEach(card => {
      const id = card.dataset.id, q = window.GA_DAYS[card.dataset.day].questions.find(x => x.id === id);
      let sel = new Set(), done = false;
      const finish = r => {
        done = true;
        const ev = evaluate(q, r), right = q.type === 'MSQ' ? q.answer : [q.answer];
        $$('.opt', card).forEach(b => { b.disabled = true; if (right.includes(b.dataset.l)) b.classList.add('right'); else if (b.classList.contains('sel')) b.classList.add('wrongsel'); });
        if (ev.st === 'correct') { S.cleared[id] = true; card.classList.remove('skipped'); card.classList.add('correct'); save(); }
        $('.pfb', card).innerHTML = `<div class="verdict ${ev.st}" style="margin-top:.8rem">${ev.st === 'correct' ? '✓ Correct — cleared from mistakes' : '✗ Not quite — answer: ' + esc(ansText(q))}</div>
          <details class="sol" open><summary>Solution</summary><div class="soltext">${q.solution}</div></details>`;
        math($('.pfb', card));
      };
      $$('.opt', card).forEach(b => (b.onclick = () => {
        if (done) return;
        if (q.type === 'MSQ') { sel.has(b.dataset.l) ? sel.delete(b.dataset.l) : sel.add(b.dataset.l); b.classList.toggle('sel'); }
        else { b.classList.add('sel'); finish(b.dataset.l); }
      }));
      const c = $('.pchk', card);
      if (c) c.onclick = () => { if (done) return; finish(q.type === 'NAT' ? $('.pin', card).value.trim() : [...sel]); };
    });
  }

  /* ---------- settings ---------- */
  function viewSettings() {
    app.innerHTML = `<h1>Settings</h1>
      <div class="card">
        <div class="form-row"><div><b>Start date</b><div class="small muted">Day 1 = this date; "today's day" counts from here.</div></div><input type="date" id="sd" value="${S.settings.startDate}"></div>
        <div class="form-row"><div><b>Test duration</b><div class="small muted">Minutes for 30 questions (GATE pace ≈ 60).</div></div>
          <select id="du">${[45, 50, 60, 75, 90].map(v => `<option ${v === S.settings.duration ? 'selected' : ''}>${v}</option>`).join('')}</select></div>
        <div class="form-row"><div><b>Show topic during test</b><div class="small muted">GATE doesn't tell you the topic — off is more realistic.</div></div><input type="checkbox" id="st" ${S.settings.showTopic ? 'checked' : ''}></div>
      </div>
      <h2 style="margin-top:2rem">Your data</h2>
      <div class="card">
        <p class="small muted" style="margin-top:0">Progress lives only in this browser (localStorage). Export a backup now and then, or to move to another device.</p>
        <div class="row"><button class="btn" id="ex">⬇ Export progress</button><label class="btn">⬆ Import<input type="file" id="im" accept="application/json" hidden></label>
          <span class="grow"></span><button class="btn danger" id="rs">Reset everything</button></div>
      </div>
      <p class="small muted" style="margin-top:2rem">Question bank: ${M.total || NDAYS * 30} questions · ${M.pyq || 0} real GATE PYQs · built ${esc(M.generated || '')}.</p>`;
    $('#sd').onchange = e => { if (e.target.value) { S.settings.startDate = e.target.value; save(true); } };
    $('#du').onchange = e => { S.settings.duration = +e.target.value; save(true); };
    $('#st').onchange = e => { S.settings.showTopic = e.target.checked; save(true); };
    $('#ex').onclick = () => {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([JSON.stringify(S, null, 1)], { type: 'application/json' }));
      a.download = `ga-daily-progress-${todayISO()}.json`; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    };
    $('#im').onchange = e => {
      const f = e.target.files[0]; if (!f) return;
      f.text().then(t => { const o = JSON.parse(t); if (!o.days || !o.settings) throw new Error('not a GA Daily export'); localStorage.setItem(KEY, JSON.stringify(o)); S = load(); alert('Progress imported.'); route(); })
        .catch(err => alert('Import failed: ' + err.message));
    };
    $('#rs').onclick = () => confirmBox('Reset all progress?', 'This deletes every attempt, note and setting in this browser. Export first if unsure.', 'Delete everything', () => { localStorage.removeItem(KEY); S = load(); save(true); closeModal(); location.hash = '#/'; });
  }

  /* ---------- modal ---------- */
  function confirmBox(title, text, ok, fn) {
    const m = $('#modal');
    m.innerHTML = `<div class="box" role="dialog" aria-modal="true"><h3>${esc(title)}</h3><p class="muted">${esc(text)}</p>
      <div class="row" style="justify-content:flex-end"><button class="btn" id="mc">Cancel</button><button class="btn primary" id="mo">${esc(ok)}</button></div></div>`;
    m.hidden = false;
    $('#mc').onclick = closeModal;
    $('#mo').onclick = () => { closeModal(); fn(); };
    m.onclick = e => { if (e.target === m) closeModal(); };
    $('#mo').focus();
  }
  function closeModal() { const m = $('#modal'); m.hidden = true; m.innerHTML = ''; }
  document.addEventListener('keydown', e => { if (e.key === 'Escape') { closeModal(); } });

  /* ---------- calculator ---------- */
  let calcEl = null;
  function closeCalc() { if (calcEl) { calcEl.remove(); calcEl = null; } }
  function toggleCalc() {
    if (calcEl) return closeCalc();
    calcEl = document.createElement('div'); calcEl.className = 'calc';
    const keys = ['7', '8', '9', '÷', '(', '4', '5', '6', '×', ')', '1', '2', '3', '−', '^', '0', '.', '%', '+', '√', 'ln', 'log', 'π', 'C', '='];
    calcEl.innerHTML = `<div class="head"><span>Calculator</span><button aria-label="Close">×</button></div>
      <input class="disp" aria-label="Expression"><div class="res"></div><div class="keys">${keys.map(k => `<button class="${k === '=' ? 'eq' : ''}">${k}</button>`).join('')}</div>`;
    document.body.appendChild(calcEl);
    const disp = $('.disp', calcEl), res = $('.res', calcEl);
    const run = () => { try { const v = calc(disp.value); res.textContent = '= ' + (Math.round(v * 1e10) / 1e10); return v; } catch (e) { res.textContent = disp.value ? 'Error' : ''; } };
    $('.head button', calcEl).onclick = closeCalc;
    disp.addEventListener('keydown', e => { e.stopPropagation(); if (e.key === 'Enter') { const v = run(); if (v !== undefined) disp.value = String(Math.round(v * 1e10) / 1e10); } });
    disp.addEventListener('input', run);
    $$('.keys button', calcEl).forEach(b => (b.onclick = () => {
      const k = b.textContent;
      if (k === 'C') { disp.value = ''; res.textContent = ''; }
      else if (k === '=') { const v = run(); if (v !== undefined) disp.value = String(Math.round(v * 1e10) / 1e10); }
      else disp.value += ({ '√': '√(', ln: 'ln(', log: 'log(' })[k] || k, run();
      disp.focus();
    }));
    disp.focus();
  }
  function calc(src) {   // tiny recursive-descent evaluator: + − × ÷ ^ % ( ) √ ln log π e
    const s = src.replace(/×/g, '*').replace(/÷/g, '/').replace(/−/g, '-').replace(/\s+/g, '');
    let i = 0;
    const peek = () => s[i], eat = c => (s[i] === c ? (i++, true) : false);
    function expr() { let v = term(); for (;;) { if (eat('+')) v += term(); else if (eat('-')) v -= term(); else return v; } }
    function term() { let v = power(); for (;;) { if (eat('*')) v *= power(); else if (eat('/')) v /= power(); else return v; } }
    function power() { const b = unary(); return eat('^') ? Math.pow(b, power()) : b; }
    function unary() { if (eat('-')) return -unary(); if (eat('+')) return unary(); return postfix(); }
    function postfix() { let v = atom(); while (eat('%')) v /= 100; return v; }
    function atom() {
      if (eat('(')) { const v = expr(); if (!eat(')')) throw 0; return v; }
      if (s.startsWith('√', i)) { i++; return Math.sqrt(atom()); }
      if (s.startsWith('ln', i)) { i += 2; return Math.log(atom()); }
      if (s.startsWith('log', i)) { i += 3; return Math.log10(atom()); }
      if (s.startsWith('π', i)) { i++; return Math.PI; }
      if (s.startsWith('pi', i)) { i += 2; return Math.PI; }
      if (peek() === 'e') { i++; return Math.E; }
      const m = /^\d*\.?\d+(e[+-]?\d+)?/.exec(s.slice(i)); if (!m) throw 0; i += m[0].length; return parseFloat(m[0]);
    }
    const v = expr(); if (i !== s.length || !isFinite(v)) throw 0; return v;
  }

  route();
})();
