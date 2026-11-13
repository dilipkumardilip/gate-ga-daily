// stdin: JSON array of TeX strings; stdout: JSON array of [index, error] for those that fail.
import katex from 'katex';
let buf = '';
process.stdin.on('data', d => (buf += d));
process.stdin.on('end', () => {
  const xs = JSON.parse(buf);
  const bad = [];
  xs.forEach((tex, i) => {
    try { katex.renderToString(tex, { throwOnError: true, strict: 'ignore' }); }
    catch (e) { bad.push([i, String(e.message || e)]); }
  });
  process.stdout.write(JSON.stringify(bad));
});
