"""Matrix gaps filled by mxfill.py: in the comparison-chip rows of "The same chip, different work", the Blender CPU, Blender GPU
and LLM columns show '–' only for the cells listed in GAPS (the gaps documented in mxfill_rows.json, with the reason there),
n/a only where the cell cannot exist, and every filled cell from mxfill.py is a dashed estimate. The new points also appear on
the LLM tab (Llama 2 7B Q4_0 model) and the Blender tab (CPU and GPU devices), and the page does not overflow at 390px."""
import asyncio, json, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
COLS={'bl-cpu':'Blender CPU','bl-gpu':'Blender GPU','llm':'LLM'}
GAPS={('llm','Intel Core Ultra 7 155H'),('llm','Intel Core Ultra 7 265K'),('llm','Intel Core Ultra 9 275HX'),('llm','Intel Core 5 320'),
      ('llm','NVIDIA GeForce RTX 4060'),('llm','NVIDIA N1X (RTX Spark)'),
      ('bl-gpu','Intel i9-9880H'),('bl-gpu','Intel Core Ultra 7 265K'),('bl-gpu','Intel Core Ultra 9 275HX'),('bl-gpu','NVIDIA GB10')}
NA={('bl-gpu','Qualcomm Snapdragon X Elite X1E-84-100')}|{('bl-cpu',c) for c in ('NVIDIA GeForce RTX 4060','NVIDIA GeForce RTX 4060 Laptop','NVIDIA GeForce RTX 4090','NVIDIA GeForce RTX 5090','NVIDIA GeForce RTX 5090 Laptop')}
FILLED={'llm':['AMD Ryzen AI Max+ 395','AMD Ryzen AI 9 HX 370','AMD Ryzen 7 8845HS','Intel Core Ultra 7 258V','Intel Core Ultra X7 358H','Qualcomm Snapdragon X Elite X1E-84-100',
               'NVIDIA GB10','NVIDIA GeForce RTX 4060 Laptop','NVIDIA GeForce RTX 4090','NVIDIA GeForce RTX 5090','NVIDIA GeForce RTX 5090 Laptop'],
        'bl-cpu':['NVIDIA N1X (RTX Spark)','Intel Core 5 320'],
        'bl-gpu':['NVIDIA GeForce RTX 4060 Laptop','NVIDIA GeForce RTX 5090','NVIDIA N1X (RTX Spark)','Intel Core 5 320']}
async def pick(pg,box,v):
    """choose v in a filter chip group as a user would: a single-choice row is clicked; a multi-select group is reset with Show all, then v alone is clicked ('' leaves every option on)"""
    if await pg.locator(f'#{box} [role=radio]').count(): await pg.click(f'#{box} [data-opt="{v}"]'); return
    if await pg.locator(f'#{box} .showall.on').count(): await pg.click(f'#{box} .showall')
    if v!='': await pg.click(f'#{box} [data-opt="{v}"]')
async def main():
    rows_gaps={tuple(k.split('|')) for k in json.load(open(HERE.parent/'mxfill_rows.json'))['gaps']}
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':1360,'height':1100}); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(INDEX+'#all'); await pg.wait_for_timeout(600)
        if rows_gaps!=GAPS: errs.append(f'gaps in mxfill_rows.json {sorted(rows_gaps)} differ from this test')
        cells=await pg.evaluate("""MROWS.filter(m=>!gen(m.c)).map(m=>({c:m.c,cells:m.cells.filter(x=>['bl-cpu','bl-gpu','llm'].includes(x.k)).map(x=>({k:x.k,t:x.td.textContent}))}))""")
        dash=set(); na=set()
        for m in cells:
            for x in m['cells']:
                if x['t']=='–': dash.add((x['k'],m['c']))
                elif x['t']=='n/a': na.add((x['k'],m['c']))
        print('comparison rows',len(cells)); print('remaining –',sorted(dash)); print('n/a',sorted(na))
        if dash!=GAPS: errs.append(f"'–' cells {sorted(dash^GAPS)} differ from the documented gaps")
        if na!=NA: errs.append(f'n/a cells changed: {sorted(na^NA)}')
        # every mxfill cell: an estimate drawn from an mx_ source, shown with ~
        for k,cs in FILLED.items():
            for c in cs:
                r=await pg.evaluate(f"(()=>{{const m=MROWS.find(m=>m.c==={c!r});if(!m)return null;const x=m.cells.find(x=>x.k==={k!r});return x&&x.r?{{src:x.r.src,est:!!x.r.est,pe:!!x.r.pe,t:x.td.textContent,cls:x.td.classList.contains('isest'),note:x.r.note,ps:!!x.r.psrc}}:{{t:x.td.textContent}}}})()")
                if not r or 'src' not in r: errs.append(f'{COLS[k]} {c}: no value ({r})'); continue
                if k=='llm' and not r['src'].startswith('mx_'): errs.append(f'{c} LLM cell not from mxfill ({r["src"]})')
                if not (r['est'] and r['pe'] and r['ps'] and r['cls'] and r['t'].startswith('~')): errs.append(f'{COLS[k]} {c}: should be a dashed est+pe estimate, got {r["t"]}')
                if k=='llm' and not any(w in r['note'] for w in ('CUDA','Vulkan','ROCm','SYCL','CPU')): errs.append(f'{c}: LLM note does not name the backend')
        # the new points on the tabs: LLM (Llama 2 7B Q4_0) and Blender (CPU and GPU)
        await pg.click('.tab[data-w="llm"]'); await pg.wait_for_timeout(250)
        await pg.select_option('#lmod','Llama 2 7B Q4_0'); await pg.wait_for_timeout(300)
        got=set(await pg.evaluate("S.pts.map(p=>p.r.chip)")); print('Llama 2 7B points',len(got))
        miss=[c for c in FILLED['llm'] if c not in got]
        if miss: errs.append('missing on the Llama 2 7B Q4_0 plot: '+', '.join(miss))
        for k in ('bl-cpu','bl-gpu'):
            await pg.click('.tab[data-w="blender"]'); await pg.wait_for_timeout(200)
            await pick(pg,'ldevw',k); await pg.wait_for_timeout(300)
            got=set(await pg.evaluate("S.pts.map(p=>p.r.chip)")); miss=[c for c in FILLED[k] if c not in got]
            if miss: errs.append(f'missing on the Blender {k} plot: '+', '.join(miss))
        # phone width: the matrix scrolls inside its box, the page does not
        pg2=await b.new_page(viewport={'width':390,'height':900}); pg2.on('pageerror',lambda e:errs.append(str(e)))
        await pg2.goto(INDEX+'#all'); await pg2.wait_for_timeout(600)
        await pg2.evaluate("document.getElementById('matrix').scrollIntoView()"); await pg2.wait_for_timeout(200)
        sw=await pg2.evaluate("[document.documentElement.scrollWidth,document.body.scrollWidth]"); print('scrollWidth at 390',sw)
        if any(w>390 for w in sw): errs.append('horizontal overflow at 390px: '+str(sw))
        print('errors',errs); await b.close()
asyncio.run(main())
