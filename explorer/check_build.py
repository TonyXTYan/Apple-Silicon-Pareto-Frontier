"""CI check: index.html matches template.html + data8.json, and the data chain reproduces data8.json.
Rebuilt numbers may differ from the committed ones in the last few digits across CPUs and maths libraries,
so they are compared with a relative tolerance. Run from anywhere: python3 explorer/check_build.py"""
import json, math, os, subprocess, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
committed_data = open('data8.json').read()
committed_page = open('index.html').read()
if committed_page != open('template.html').read().replace('/*DATA*/', committed_data):
    sys.exit('index.html is stale: run python3 explorer/build.py and commit the result')
subprocess.run([sys.executable, 'build.py'], check=True, stdout=subprocess.DEVNULL)
bad = []
def cmp(a, b, path):
    if isinstance(a, dict) and isinstance(b, dict):
        if a.keys() != b.keys(): bad.append(f'{path}: keys differ'); return
        for k in a: cmp(a[k], b[k], f'{path}.{k}')
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b): bad.append(f'{path}: length {len(a)} vs {len(b)}'); return
        for i, (x, y) in enumerate(zip(a, b)): cmp(x, y, f'{path}[{i}]')
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        if not math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12): bad.append(f'{path}: {a} vs {b}')
    elif a != b: bad.append(f'{path}: {a!r} vs {b!r}')
cmp(json.loads(committed_data), json.loads(open('data8.json').read()), 'data')
# leave the committed files in place so the deployed page is exactly what was committed
open('data8.json', 'w').write(committed_data); open('index.html', 'w').write(committed_page)
if bad: sys.exit('data chain no longer reproduces data8.json:\n' + '\n'.join(bad[:30]))
print('ok: index.html is current and the data chain reproduces data8.json')
