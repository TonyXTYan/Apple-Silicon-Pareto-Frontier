# Apple Silicon work per joule

An interactive, single-file page that compares how much computing each Apple Silicon Mac gets out of a joule taken from the wall. It covers eight workloads: CPU all cores, CPU one thread, HPL, numerical libraries (GEMM), gaming (Cyberpunk 2077, Baldur's Gate 3, Assassin's Creed Shadows), Blender CPU and Blender GPU (one Blender tab, with a Scene menu) and LLM generation. Thirteen Intel, AMD, Qualcomm and NVIDIA machines are shown alongside for comparison. A separate Numerical libraries tab compares matrix-multiply speed with Accelerate, OpenBLAS and Metal; it is kept out of the All view and the matrix because none of its power is measured. Every point carries uncertainties, and every point can be compared against a chosen baseline machine (the page opens on LLM generation with no baseline, in absolute units).

**Live page:** https://tonyxtyan.github.io/Apple-Silicon-Pareto-Frontier/

## Layout

```
explorer/
  template.html        page: HTML + CSS + JS; the literal /*DATA*/ is replaced by data10.json
  index.html           built page (self-contained, open it directly)
  data10.json          final data (rows = measured, est = estimates, sources, loo, apple specs)
  build.py             runs the whole data chain and rebuilds index.html
  gen_data.py          -> data.json   measured rows (Cinebench, HPL, Cyberpunk, metered LLM), reusing plot/all.py rows
  model.py             -> data2.json  hierarchical ridge model in log space, leave-one-out errors, estimates, Apple power specs, power modes
  llm.py               -> data3.json  llama.cpp thread (Llama 2 7B Q4_0, 20 chips) with estimated decode power
  blender.py           -> data4.json  Blender Open Data 4.5 medians (CPU, Metal), three-scene sum and per scene, with estimated power
  i9.py                -> data5.json  Intel i9-9880H MacBook Pro 16 (2019) baseline rows
  llm2.py              -> data6.json  XiongjieDai llama-bench sweeps (Llama 3 8B/70B, Q4_K_M/F16, tg512..8192)
  llm3.py              -> data7.json  MLX vs GGUF pairs; 4x M3 Ultra cluster (exo RDMA vs llama.cpp RPC)
  games.py             -> data8.json  Baldur's Gate 3 and AC Shadows frame rates; `game` field on gpu rows
  numerics.py          -> data9.json  numerical libraries: fp32 GEMM Accelerate vs OpenBLAS (Julia), CPU vs GPU SGEMM (arXiv 2502.05317), fp64 DGEMM
  x86.py               -> data10.json Intel, AMD, Qualcomm and NVIDIA comparison machines, from x86_rows.json
  x86_rows.json        the researched comparison rows used (each with its source URL and notes)
  tests/*.py           Playwright smoke tests; screenshots go to tests/shots/
plot/
  all.py               original static plot + the measured-row table used by gen_data.py
  *.csv, *.png         static outputs from the first version
```

## Build and test

```
cd explorer
pip install -r ../requirements.txt   # numpy, matplotlib, adjustText
python3 build.py                  # regenerates data*.json and index.html (reproduces the shipped data10.json exactly)
pip install playwright && python3 -m playwright install chromium   # or set CHROME=/path/to/chrome
python3 tests/i9_baseline.py      # every test prints "errors []" when the page has no JS errors
```

Quick syntax check of the page script:
`python3 -c "s=open('index.html').read();a=s.index('<script>')+8;open('/tmp/x.js','w').write(s[a:s.index('</script>',a)])" && node --check /tmp/x.js`

## Data model (one row per machine and workload)

- `w`: workload (`cpu-all`, `cpu-one`, `hpl`, `gpu`, `bl-cpu`, `bl-gpu`, `llm`, and `blas` for the Numerical libraries tab).
- `x`: throughput. `e`: work per joule. `p`: wall power in W. Bounds are given by `xlo/xhi`, `elo/ehi`, `plo/phi`.
- `est`: an estimate. Hidden unless the "Model estimates" switch is on, except rows with `pe` (speed measured, power estimated), which always show.
- `game` (gpu rows only): `Cyberpunk 2077`, `Baldur's Gate 3` or `Assassin's Creed Shadows`. The matrix and the All view use Cyberpunk only.
- `set` and `lib` (blas rows only): `julia-sgemm`, `arxiv-sgemm` or `julia-dgemm`, and the library (`OpenBLAS`, `Accelerate`, `Accelerate (CPU)`, `MPS (GPU)`, `DGEMM fp64`). Pairs on one machine share `grp`, ordered OpenBLAS→Accelerate and CPU→GPU.
- `scene` (bl-cpu and bl-gpu rows only): `monster`, `junkshop` or `classroom`; rows without it are the three-scene sum, which is what the matrix and the All view use. Blender rows also carry `grp`/`ord` so each chip's CPU and GPU point are joined.
- `tier`: `base`, `Pro`, `Max`, `Ultra` for Apple chips; the vendor (`Intel`, `AMD`, `Qualcomm`, `NVIDIA`) for comparison chips, whose names start with the vendor and count as generation 0. Comparison rows also carry `sl`/`sd`, short chip and machine labels for the plot.
- `resc`: the score was converted from Cinebench R23 (drawn hollow). `q`: quality grade; a measured row below 'A', or a speed-measured `pe` row graded 'B' or 'C' (for example a Blender median over three runs or fewer), gets a "weaker measurement" ring. Plain estimates are 'E'.
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
  - Scenes: per-scene medians (monster, junkshop, classroom) from the full Open Data snapshot (Blender 4.5.0, CC0, generated 2026-11-21); each scene reuses the power of the three-scene point. Their sum is within about 2% of the published three-scene median (the median of a sum is not the sum of medians). GPU points are each chip's full-core GPU (the 8-core M2 where the borrowed power is the 8-core MacBook Air). Cut-down GPU variants in Open Data (M1 7c, M1 Pro 14c, M1 Max 24c, M1 Ultra 48c, M2 Pro 16c, M2 Max 30c, M2 Ultra 60c, M3 8c, M3 Pro 14c, M3 Max 30c, M3 Ultra 60c, M4 8c, M4 Pro 16c, M4 Max 32c, M5 Pro 16c, M5 Max 32c) are left out: no machine with them has a measured or modelled power here, and the chip names on the page encode CPU, not GPU, core counts. Medians over three runs or fewer are graded 'B' (M5 Ultra and M6 on both devices, M5 Pro GPU).
- **Comparison machines (x86.py):** the 13-machine shortlist of the research (Framework Desktop and ROG Flow Z13 with the Ryzen AI Max+ 395; Dell Pro Max with GB10; Geerling's Core Ultra 7 265K + RTX 4090 desktop; Zenbook S 14 with the Core Ultra 7 258V; Zenbook S 16 with the Ryzen AI 9 HX 370; XMG Evo 15 with the Core Ultra 7 155H; VIA 14 Pro with the Ryzen 7 8845HS; Minisforum M2 Pro with the Core Ultra X7 358H; Galaxy Book4 Edge 16 with the Snapdragon X Elite X1E-84-100; XMG Neo 16 E25 with the Core Ultra 9 275HX and RTX 5090 Laptop; ProArt P16 with the HX 370 and RTX 5090 Laptop; Dell XPS 13 with the Core 5 320), with every workload each has: Notebookcheck Cinebench 2024 and Cyberpunk 2077 wall power (external monitor), Geerling HPL (average wall power) and LLM runs (peak wall power, so lower bounds, graded 'B' like the M3 Ultra runs). The chip is the processor doing the work, so a discrete-GPU machine's Cyberpunk and LLM rows sit under its NVIDIA GPU and its CPU rows under its Intel or AMD CPU; that wall power still covers the whole laptop or PC. Rows whose power is a stand-in from another test (Framework Desktop and XMG Neo 16 E25 Cinebench) are graded 'B'. Some Cyberpunk frame rates are the review's own 1080p ultra result, which runs 5–15% above the efficiency-chart basis used for the Macs (noted per point); the Snapdragon runs Cyberpunk under emulation. Blender Open Data medians (Blender 4.5.0) for these chips use the Apple rules (0.9–1.1× Cinebench, 0.45–0.95× Cyberpunk wall power) with the research's proxy machine where it is on the page, otherwise the shortlisted machine with that chip; the 275HX (Cinebench power itself a stand-in), the 265K (HPL power stands in) and the desktop RTX 4090 (power from Notebookcheck's own 9800X3D test PC) are graded 'B'. They appear only in the three-scene view of the Blender tab. Left out: the Snapdragon's Blender median (Open Data lists the X1E-80, not the X1E-84, under several names); the 14900HX, 285H, 285K and 9950X machines and the RTX 4060/4080/5070/5080 laptops, which are not in the shortlist; the Framework 13 (the shortlist allows the XPS 13 or the Framework 13); and the TDP sweeps (noted on the HX 370, 8845HS and 155H points). No comparison machine is in the Llama 2 7B Q4_0 all-chip set; the RTX 4090 ran Q4_K_M.
- **Numerical libraries:** no wall power was metered for any run, and each speed is one community or paper run, so every point is `pe`. Power = 0.5–1.4× (log-centred 0.84) the Cinebench 2024 all-core wall power on this page of the same chip: the named machine where the source names one (Hubner et al.: M1 and M3 MacBook Air 13, M2 and M4 Mac mini), otherwise the chip's best-measured machine (Cinebench 2024 before R23-converted rows, then the narrowest power range; the M3 Ultra uses its model estimate). The band is wide because Accelerate GEMM stops scaling after about two threads (AppleAccelerate.jl benchmarks), which argues for less than Cinebench power, while HPL draws 1.1–1.4× Cinebench power on the M4 Mac mini and M1 Max Mac Studio. 5% is allowed for run-to-run speed spread. The main set is the Julia Discourse AppleNeuralEngine.jl thread (https://discourse.julialang.org/t/-/140344), fp32 GEMM at 2048³ (the size every chip ran; 1024³ figures are in the source too) with Accelerate and OpenBLAS on ten chips; both libraries get the same power, so their efficiency ratio is their speed ratio. The second set is Hubner et al., arXiv 2502.05317, peak SGEMM with Accelerate on the CPU and MPS on the GPU on the M1–M4 base chips; their powermetrics package efficiency (0.2–0.46 TFLOPS/W) is an upper bound and is quoted in each note. The third is three fp64 DGEMM runs on the performance cores (Julia Discourse thread 128459). Left out: MATLAB and Mathematica results (benchmarks in images, or scores confounded by version and kernel count), PyTorch matmul lists with anomalous or unlabelled devices, single-chip sets, and the Ryzen 9 9950X DGEMM reference.
- **Clusters:**
  - exo (tensor parallel): N × 110–240 W.
  - llama.cpp RPC (layer split): one busy node plus (N−1) idle nodes.
- **MLX vs GGUF:** equal power is assumed, so the efficiency ratio equals the speed ratio.
- **Other games (gaming tab):** Notebookcheck frame rates for Baldur's Gate 3 (Ultra, TAA) and Assassin's Creed Shadows (Ultra High), 1080p, on the nine machines with a metered Cyberpunk row (AC Shadows has no M4 Pro or M4 Mac mini result). No wall power was published in these games, so each point borrows that machine's Cyberpunk wall power, with 12% added in quadrature to the log power spread and 3% for the frame rate; they are `pe` rows (speed measured, power estimated). On the M5 Air the chip drew slightly more in BG3 than in Cyberpunk. The M5 Max MacBook Pro 14 is adapter-capped (97 W), so it keeps its `ex` flag. Older M4 reviews may have used translated builds (the M4 Mac mini's Cyberpunk run was emulated; BG3 is native). Left out: Total War: Pharaoh, which is engine-limited near 50 to 56 fps from the M4 Pro to the M5 Max and so says little about the GPU; Shadow of the Tomb Raider, which has no M5, M5 Pro or M5 Max results; machines without a Cyberpunk row on the page (M4 MacBook Air 13 and MacBook Pro 14, M5 Pro MacBook Pro 14); and MetalFX or frame-generation results and Geekerwan's chip-power figures.

## Page features

- **Tabs and baseline:** one tab per workload plus All workloads; Blender CPU and GPU share one tab. The baseline menu switches to ratios; None gives absolute units.
- **Blender tab:** CPU renders are dashed rings, GPU renders are filled, and a thin line joins each chip's pair. A **Scene** menu shows the three-scene sum (the default, as in the matrix) or one scene; a **Device** menu shows CPU, GPU or both. Frontiers are per device; baselines compare the same scene on the same device. Old `#bl-cpu` and `#bl-gpu` links open the tab on that device.
- **All workloads with None:** stacked per-workload scales.
- **Hover:** shows relatives and the exact power line. Click a point to pin it. Hover highlights: related chips, same chip, same chip and machine, or same benchmark (same model, game, scene and device, set and library, or workload).
- **Chart navigation:** zoom, pan and pinch; full screen.
- **Efficiency frontier:** straight Pareto segments with fitted ends (exponential by default; also power law, log or linear). It is drawn separately for each workload, each LLM model, each game and each Blender device.
- **Matrix:** chip × workload, with estimates and ratio ± uncertainty.
- **Leave-one-out plot:** shows both error bars and can be enlarged.
- **Set menu (Numerical libraries tab):** fp32 GEMM Accelerate vs OpenBLAS (default), CPU vs GPU peak SGEMM, fp64 DGEMM, or every set. Frontiers are per set and library; baselines compare the same set and library.
- **Game menu (gaming tab):** every game, or one. Frontiers are drawn per game. A baseline divides each game by that machine in the same game, so the baseline sits at 1× in every game; with every game shown, frame rate stays absolute and the constant-power lines are hidden (they differ per game). Games the baseline has no reading for are dropped while it is set.
- **LLM Model menu:** 7B all-chip set, context sweeps, MLX vs GGUF, clusters. **Model size** chips filter by total parameters: XS <2B, S 2–5B, M 5–12B, L 12–50B, XL 50–150B, XXL 150–500B, XXXL ≥500B.
- **Palette:** colours come from the dataviz skill's validated palette. Intel is #c2418f in light mode and #b84a8c in dark; in light mode Pro is #e05a1a and Max is darkened to #2a925c for 3:1 contrast on the white plot field. The comparison vendors were found by a search over hues, scored with the dataviz validator's OKLab metric against the five existing colours and each other in both themes: AMD brick #943207 / brown #85552e, Qualcomm violet #430ceb / #8c0cf5, NVIDIA purple #7c0899 / pink #f525cb (light / dark). Every pair involving a new colour keeps normal-vision ΔE ≥ 15.0, protan/deutan ΔE ≥ 8.3 and tritan ΔE ≥ 6.7 (OKLab ×100), no worse than the existing Apple pairs (Intel–Max 6.8 protan/deutan, base–Max 4.0 tritan), and contrast on the plot field is ≥ 3:1 in both themes (dark AMD 3.01, dark Qualcomm 3.14). With nine colours a scatter cannot pass every all-pairs gate, so the chip-tier chips, labels and table names carry the vendor too.
- **Comparison chips:** the chip-tier chips include Intel, AMD, Qualcomm and NVIDIA; the baseline menu lists them in one group per vendor; the matrix lists them after the Apple chips under a divider; hovering one draws lines to the other chips of the same vendor.
