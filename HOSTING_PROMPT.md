I have a finished static website (plain HTML/CSS/JS, no build step) in this folder:
/Users/dilipkumar/Downloads/GATE2027/Aptitude/DailyTest

Please put it in a PRIVATE GitHub repository on my personal account and host it so I can open it from any device. Do it end to end and give me the final URL.

Facts about the project:
- The website itself is the `site/` subfolder (index.html, app.js, charts.js, styles.css, vendor/katex, data/, img/). About 6.5 MB, ~370 files. It needs no build, no server code and no environment variables. All paths are relative, and data is loaded with <script> tags (no fetch), so it works from any sub-path.
- The rest of the folder (bank/, tools/, review/, BRIEF.md, README.md…) is the source and tooling. Commit it too, but do NOT commit `tools/.venv/` (200 MB Python venv) or `tools/node_modules/`. Add a .gitignore with: tools/.venv/, tools/node_modules/, __pycache__/, .DS_Store
- User progress is stored in the browser's localStorage, so nothing server-side is needed.

Steps:
1. `git init` in that folder, add the .gitignore, make the first commit, and create a private repo named `gate-ga-daily` on my GitHub account (use the `gh` CLI if it is installed and logged in; otherwise tell me exactly what to click).
2. Hosting — check which applies and tell me before choosing:
   - GitHub Pages works on a PRIVATE repo only if my account has GitHub Pro (or Team/Enterprise). If I have it: deploy the `site/` folder with a GitHub Actions workflow (`.github/workflows/pages.yml` using actions/configure-pages, actions/upload-pages-artifact with `path: site`, actions/deploy-pages), and set Pages → Source = "GitHub Actions". Add an empty `site/.nojekyll`.
   - If I don't have Pro, keep the repo private and deploy it free with Cloudflare Pages or Netlify connected to the repo: framework "None", no build command, output/publish directory `site`. (Only make the repo public if I explicitly say so; it contains my question bank.)
3. Open the deployed URL and verify: the home page shows "Day 1 of 60" and a 60-day grid; open Day 1 → Start test; questions show math rendered (no raw `$...$`), Q6–Q7 show bar/pie charts, Q30 shows figures; the browser console has no 404s for data/days/day01.js, vendor/katex files or img/ files.
4. Give me: the repo URL, the live website URL, and the 2–3 commands to publish future changes (git add/commit/push — the deploy should then update automatically).

Do not change any file inside `site/`, `bank/` or `tools/` except adding `site/.nojekyll`. Don't re-run any of the Python tools.
