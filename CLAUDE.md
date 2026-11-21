# Notes for Claude

The site at https://tonyxtyan.github.io/Apple-Silicon-Pareto-Frontier/ is `explorer/index.html`, deployed by `.github/workflows/pages.yml` on push to `main`.

## After any change to the page or data

1. Edit `explorer/template.html` (or the data scripts), never `explorer/index.html` directly.
2. `pip install -r requirements.txt`, then `python3 explorer/build.py`. CI (`explorer/check_build.py`) fails if `index.html` is stale or the data chain no longer reproduces the final data file (`data14.json`).
3. Run the smoke tests in `explorer/tests/` (each prints `errors []`).
4. Commit and push.
