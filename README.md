# Apple Silicon work per joule

An interactive, single-file page that compares how much computing each Apple Silicon Mac gets out of a joule taken from the wall. It covers seven workloads: CPU all cores, CPU one thread, HPL, Cyberpunk GPU, Blender CPU, Blender GPU and LLM generation. Every point carries uncertainties, and every point can be compared against a chosen baseline machine (by default the M4 Max MacBook Pro 16).

**Live page:** https://tonyxtyan.github.io/Apple-Silicon-Pareto-Frontier/

## Layout

```
explorer/
  template.html        page: HTML + CSS + JS; the literal /*DATA*/ is replaced by data7.json
  index.html           built page (self-contained, open it directly)
  data7.json           final data (rows = measured, est = estimates, sources, loo, apple specs)
  build.py             runs the whole data chain and rebuilds index.html
  gen_data.py          -> data.json   measured rows (Cinebench, HPL, Cyberpunk, metered LLM), reusing plot/all.py rows
  model.py             -> data2.json  hierarchical ridge model in log space, leave-one-out errors, estimates, Apple power specs, power modes
  llm.py               -> data3.json  llama.cpp thread (Llama 2 7B Q4_0, 20 chips) with estimated decode power
  blender.py           -> data4.json  Blender Open Data 4.5 medians (CPU, Metal) with estimated power
  i9.py                -> data5.json  Intel i9-9880H MacBook Pro 16 (2019) baseline rows
  llm2.py              -> data6.json  XiongjieDai llama-bench sweeps (Llama 3 8B/70B, Q4_K_M/F16, tg512..8192)
  llm3.py              -> data7.json  MLX vs GGUF pairs; 4x M3 Ultra cluster (exo RDMA vs llama.cpp RPC)
  tests/*.py           Playwright smoke tests; screenshots go to tests/shots/
plot/
  all.py               original static plot + the measured-row table used by gen_data.py
  *.csv, *.png         static outputs from the first version
```

## Build and test

```
cd explorer
pip install -r ../requirements.txt   # numpy, matplotlib, adjustText
python3 build.py                  # regenerates data*.json and index.html (reproduces the shipped data7.json exactly)
pip install playwright && python3 -m playwright install chromium   # or set CHROME=/path/to/chrome
python3 tests/i9_baseline.py      # every test prints "errors []" when the page has no JS errors
```

Quick syntax check of the page script:
`python3 -c "s=open('index.html').read();a=s.index('<script>')+8;open('/tmp/x.js','w').write(s[a:s.index('</script>',a)])" && node --check /tmp/x.js`

## Data model (one row per machine and workload)

- `w`: workload (`cpu-all`, `cpu-one`, `hpl`, `gpu`, `bl-cpu`, `bl-gpu`, `llm`).
- `x`: throughput. `e`: work per joule. `p`: wall power in W. Bounds are given by `xlo/xhi`, `elo/ehi`, `plo/phi`.
- `est`: an estimate. Hidden unless the "Model estimates" switch is on, except rows with `pe` (speed measured, power estimated), which always show.
- `resc`: the score was converted from Cinebench R23 (drawn hollow). `q`: quality grade; anything below 'A' gets a "weaker measurement" ring.
- LLM extras:
  - `model`: model name.
  - `set`: `sweep`, `mlx` or `cluster`. These sets are kept out of the All view.
  - `grp`/`ord`: joined by lines in order.
  - `ctx`, `eng`, `nodes`.

Units are chosen so that x / e = wall power in watts. That is why the constant-power diagonals work: Blender uses samples/s (the Open Data score ÷ 60).

## Key modelling choices (details in each point's note)

- **Measured wall power:** Notebookcheck (external monitor) for CPU and Cyberpunk; Jeff Geerling for HPL, M3 Ultra LLM and the cluster.
- **Cinebench:** R23 → 2024 is stitched through the M4 Mac mini (about 5–6% rms). The Intel i9 uses the x86 ratio instead.
- **Estimate model:** log e = workload + tier×workload + generation + tier + chip, ridge-regularised. Its leave-one-out rms sets the error bars. Apple's rated maximum power gives a lower bound on e.
- **LLM decode power:** 0.75–1.1 × GPU-load wall power, calibrated on the M4 and M6 Mac mini.
- **Blender power:**
  - CPU: 0.9–1.1 × Cinebench wall power.
  - GPU: 0.45–0.95 × Cyberpunk wall power, anchored only by Eclectic Light's ~20 W GPU reading.
- **Clusters:**
  - exo (tensor parallel): N × 110–240 W.
  - llama.cpp RPC (layer split): one busy node plus (N−1) idle nodes.
- **MLX vs GGUF:** equal power is assumed, so the efficiency ratio equals the speed ratio.

## Page features

- **Tabs and baseline:** one tab per workload plus All workloads. The baseline menu switches to ratios; None gives absolute units.
- **All workloads with None:** stacked per-workload scales.
- **Hover:** shows relatives and the exact power line. Click a point to pin it.
- **Chart navigation:** zoom, pan and pinch; full screen.
- **Efficiency frontier:** straight Pareto segments with fitted ends (exponential by default; also power law, log or linear). It is drawn separately for each workload and each LLM model.
- **Matrix:** chip × workload, with estimates and ratio ± uncertainty.
- **Leave-one-out plot:** shows both error bars and can be enlarged.
- **LLM Model menu:** 7B all-chip set, context sweeps, MLX vs GGUF, clusters.
- **Palette:** colours come from the dataviz skill's validated palette. Intel is #c2418f in light mode and #b84a8c in dark; the light-mode Max green is darkened to #16a372 for 3:1 contrast on the white plot field.
