/* Minimal SVG chart renderer for Data Interpretation questions.
   spec: {type: bar|groupbar|stackbar|line|pie, title, labels[], series:[{name, values[]}], xLabel, yLabel} */
(function () {
  const COLORS = ['#5E8B7E', '#7FA7C4', '#D9B86C', '#C98B7E', '#9C88B5', '#8FB39A', '#B7A57A'];
  const INK = '#2F3A3A', SOFT = '#6B7776', GRID = '#E4E9E6';
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const fmt = v => (Math.round(v * 100) / 100).toLocaleString('en-IN');

  function niceMax(m) {
    if (m <= 0) return 1;
    const p = Math.pow(10, Math.floor(Math.log10(m)));
    for (const k of [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]) if (k * p >= m) return k * p;
    return 10 * p;
  }
  function ticks(max) { const n = 5; return Array.from({ length: n + 1 }, (_, i) => (max / n) * i); }

  function legend(series, x, y) {
    let out = '', cx = x;
    series.forEach((s, i) => {
      out += `<rect x="${cx}" y="${y - 9}" width="12" height="12" rx="3" fill="${COLORS[i % COLORS.length]}"/>` +
        `<text x="${cx + 17}" y="${y + 1}" font-size="12" fill="${INK}">${esc(s.name || '')}</text>`;
      cx += 30 + String(s.name || '').length * 7;
    });
    return out;
  }

  function axes(spec, W, H, L, T, R, B, ymax) {
    let g = '';
    for (const t of ticks(ymax)) {
      const y = T + (H - T - B) * (1 - t / ymax);
      g += `<line x1="${L}" x2="${W - R}" y1="${y}" y2="${y}" stroke="${GRID}"/>` +
        `<text x="${L - 6}" y="${y + 4}" font-size="11" fill="${SOFT}" text-anchor="end">${fmt(t)}</text>`;
    }
    g += `<line x1="${L}" x2="${W - R}" y1="${H - B}" y2="${H - B}" stroke="${SOFT}"/>`;
    if (spec.yLabel) g += `<text transform="translate(14 ${T + (H - T - B) / 2}) rotate(-90)" font-size="12" fill="${SOFT}" text-anchor="middle">${esc(spec.yLabel)}</text>`;
    if (spec.xLabel) g += `<text x="${L + (W - L - R) / 2}" y="${H - 6}" font-size="12" fill="${SOFT}" text-anchor="middle">${esc(spec.xLabel)}</text>`;
    return g;
  }

  function barLike(spec) {
    const labels = spec.labels || [], series = spec.series || [];
    const stacked = spec.type === 'stackbar';
    const n = labels.length, k = series.length;
    const W = Math.max(520, n * (stacked || spec.type === 'bar' ? 70 : 40 + 26 * k)), H = 330;
    const T = series.length > 1 ? 44 : 24, B = 54, L = 58, R = 16;
    let max = 0;
    for (let i = 0; i < n; i++) {
      if (stacked) max = Math.max(max, series.reduce((a, s) => a + (+s.values[i] || 0), 0));
      else series.forEach(s => (max = Math.max(max, +s.values[i] || 0)));
    }
    const ymax = niceMax(max * 1.08);
    const ph = H - T - B, slot = (W - L - R) / n;
    const y = v => T + ph * (1 - v / ymax);
    let g = axes(spec, W, H, L, T, R, B, ymax);
    for (let i = 0; i < n; i++) {
      const x0 = L + slot * i;
      if (stacked) {
        const bw = Math.min(46, slot * .6); let acc = 0;
        series.forEach((s, j) => {
          const v = +s.values[i] || 0, y1 = y(acc + v), y0 = y(acc);
          g += `<rect x="${x0 + (slot - bw) / 2}" y="${y1}" width="${bw}" height="${Math.max(0, y0 - y1)}" fill="${COLORS[j % COLORS.length]}"/>`;
          if (y0 - y1 > 14) g += `<text x="${x0 + slot / 2}" y="${(y0 + y1) / 2 + 4}" font-size="11" fill="#fff" text-anchor="middle">${fmt(v)}</text>`;
          acc += v;
        });
        g += `<text x="${x0 + slot / 2}" y="${y(acc) - 5}" font-size="11.5" font-weight="600" fill="${INK}" text-anchor="middle">${fmt(acc)}</text>`;
      } else {
        const bw = Math.min(k === 1 ? 46 : 28, (slot * .78) / k);
        const start = x0 + (slot - bw * k) / 2;
        series.forEach((s, j) => {
          const v = +s.values[i] || 0, bx = start + j * bw;
          g += `<rect x="${bx + 1}" y="${y(v)}" width="${bw - 2}" height="${Math.max(0, y(0) - y(v))}" rx="2" fill="${COLORS[j % COLORS.length]}"/>` +
            `<text x="${bx + bw / 2}" y="${y(v) - 5}" font-size="${k > 2 ? 10 : 11.5}" fill="${INK}" text-anchor="middle">${fmt(v)}</text>`;
        });
      }
      g += `<text x="${x0 + slot / 2}" y="${H - B + 17}" font-size="12" fill="${INK}" text-anchor="middle">${esc(labels[i])}</text>`;
    }
    if (series.length > 1) g += legend(series, L, 18);
    return wrap(W, H, g, spec);
  }

  function line(spec) {
    const labels = spec.labels || [], series = spec.series || [], n = labels.length;
    const W = Math.max(520, n * 64), H = 330, T = series.length > 1 ? 44 : 24, B = 54, L = 58, R = 24;
    let max = 0; series.forEach(s => s.values.forEach(v => (max = Math.max(max, +v))));
    const ymax = niceMax(max * 1.1), ph = H - T - B, slot = (W - L - R) / n;
    const y = v => T + ph * (1 - v / ymax), x = i => L + slot * (i + .5);
    let g = axes(spec, W, H, L, T, R, B, ymax);
    labels.forEach((lab, i) => (g += `<text x="${x(i)}" y="${H - B + 17}" font-size="12" fill="${INK}" text-anchor="middle">${esc(lab)}</text>`));
    series.forEach((s, j) => {
      const c = COLORS[j % COLORS.length];
      g += `<polyline fill="none" stroke="${c}" stroke-width="2.4" points="${s.values.map((v, i) => `${x(i)},${y(+v)}`).join(' ')}"/>`;
      s.values.forEach((v, i) => {
        g += `<circle cx="${x(i)}" cy="${y(+v)}" r="4" fill="#fff" stroke="${c}" stroke-width="2"/>` +
          `<text x="${x(i)}" y="${y(+v) + (j % 2 ? 17 : -9)}" font-size="11" fill="${INK}" text-anchor="middle">${fmt(+v)}</text>`;
      });
    });
    if (series.length > 1) g += legend(series, L, 18);
    return wrap(W, H, g, spec);
  }

  function pie(spec) {
    const labels = spec.labels || [], vals = (spec.series && spec.series[0] ? spec.series[0].values : []).map(Number);
    const tot = vals.reduce((a, b) => a + b, 0) || 1;
    const W = 560, H = 320, cx = 160, cy = 160, r = 130;
    let g = '', a0 = -Math.PI / 2;
    vals.forEach((v, i) => {
      const a1 = a0 + (v / tot) * Math.PI * 2, large = a1 - a0 > Math.PI ? 1 : 0;
      const p = (a, rr) => [cx + rr * Math.cos(a), cy + rr * Math.sin(a)];
      const [x0, y0] = p(a0, r), [x1, y1] = p(a1, r);
      g += vals.length === 1 ? `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${COLORS[0]}"/>` :
        `<path d="M${cx},${cy} L${x0},${y0} A${r},${r} 0 ${large} 1 ${x1},${y1} Z" fill="${COLORS[i % COLORS.length]}" stroke="#fff" stroke-width="2"/>`;
      if (v / tot > .045) { const [tx, ty] = p((a0 + a1) / 2, r * .64); g += `<text x="${tx}" y="${ty + 4}" font-size="12" font-weight="600" fill="#fff" text-anchor="middle">${fmt(v)}</text>`; }
      a0 = a1;
    });
    labels.forEach((lab, i) => {
      const yy = 40 + i * 24;
      g += `<rect x="320" y="${yy - 11}" width="13" height="13" rx="3" fill="${COLORS[i % COLORS.length]}"/>` +
        `<text x="340" y="${yy}" font-size="12.5" fill="${INK}">${esc(lab)}: <tspan font-weight="600">${fmt(vals[i])}</tspan></text>`;
    });
    return wrap(W, Math.max(H, 40 + labels.length * 24), g, spec);
  }

  function wrap(W, H, g, spec) {
    const title = spec.title ? `<div class="small muted" style="text-align:center;margin-bottom:.2rem;font-weight:600">${esc(spec.title)}</div>` : '';
    return `${title}<svg viewBox="0 0 ${W} ${H}" width="${W}" role="img" aria-label="${esc(spec.title || 'chart')}" font-family="Inter, sans-serif">${g}</svg>`;
  }

  window.GACharts = {
    render(spec) {
      try {
        if (!spec) return '';
        if (spec.type === 'pie') return pie(spec);
        if (spec.type === 'line') return line(spec);
        return barLike(spec);
      } catch (e) { return '<p class="muted">[chart could not be drawn]</p>'; }
    }
  };
})();
