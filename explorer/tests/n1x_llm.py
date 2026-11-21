"""N1X (RTX Spark) LLM generation (n1xllm.py): the seven N1X LLM points from n1xllm_rows.json are on the LLM tab, each under its
own model in the Model menu next to the other chips running that model; the one run with its own power (Frandroid's ProArt P16 on
battery) is measured, the others are dashed est+pe points with power borrowed from the laptop's Cyberpunk wall power and a source
for both; every point is grade B, none uses a GB10 source, and none is a Llama 2 7B Q4_0 point, so the matrix LLM cell of the N1X
stays '–' (a documented gap in mxfill_rows.json). The page does not overflow at 390px."""
import asyncio, json, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
N1='NVIDIA N1X (RTX Spark)'; PA,SU='Asus ProArt P16 H7607 (RTX Spark)','Microsoft Surface Laptop Ultra (2026)'
# model -> [(device, measured power?)]; the model names are those already on the page, so each joins other chips' points
WANT={'Qwen3.6 35B-A3B':[(PA,True),(PA,False),(SU,False)],'Qwen3 8B':[(PA,False)],'Qwen3.8 27B':[(PA,False)],
      'gpt-oss 120B':[(PA,False)],'gpt-oss 20B (Ollama)':[(SU,False)]}
async def main():
    rows=json.load(open(HERE.parent/'n1xllm_rows.json'))['rows']
    gaps=json.load(open(HERE.parent/'mxfill_rows.json'))['gaps']
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':1360,'height':1100}); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(INDEX+'#llm'); await pg.wait_for_timeout(600)
        if len(rows)!=sum(len(v) for v in WANT.values()): errs.append(f'{len(rows)} rows in n1xllm_rows.json, test expects {sum(len(v) for v in WANT.values())}')
        n1=await pg.evaluate(f"""ALL.filter(r=>r.w==='llm'&&r.chip==='{N1}'&&r.src.startsWith('n1x_')).map(r=>({{m:r.model,d:r.dev,est:!!r.est,pe:!!r.pe,q:r.q,ps:r.psrc||'',
            src:SRC[r.src]?SRC[r.src].url:'',pss:r.psrc&&SRC[r.psrc]?SRC[r.psrc].url:'',x:r.x,e:r.e,p:r.p,elo:r.elo,ehi:r.ehi}}))""")
        print('N1X LLM points',len(n1))
        for x in n1: print(f"  {x['m']:22} {x['d'][:36]:36} x={x['x']:<5} p={x['p']:<6} e={x['e']} [{x['elo']},{x['ehi']}] {'est+pe' if x['pe'] else 'measured'} {x['q']}")
        got=sorted((x['m'],x['d'],not x['pe']) for x in n1); want=sorted((m,d,meas) for m,v in WANT.items() for d,meas in v)
        if got!=want: errs.append(f'N1X LLM points {got} differ from {want}')
        for x in n1:
            if x['q']!='B': errs.append(f"{x['m']} on {x['d']}: grade {x['q']}, expected B")
            if not x['src'].startswith('https://') or 'dgx' in x['src'].lower(): errs.append(f"{x['m']}: bad source {x['src']}")
            if not (x['elo']<x['e']<x['ehi']): errs.append(f"{x['m']} on {x['d']}: e outside its range")
            if x['pe'] and not (x['est'] and x['pss'].startswith('https://www.notebookcheck.net/')): errs.append(f"{x['m']} on {x['d']}: borrowed power without a Notebookcheck power source")
            if x['m']=='Llama 2 7B Q4_0': errs.append('an N1X Llama 2 7B Q4_0 point appeared; update the matrix gap')
        # each model in the Model menu: the N1X points sit with the other chips of that model (they share a frontier)
        opts=await pg.evaluate("[...document.querySelectorAll('#lmod option')].map(o=>o.value)")
        for m,v in WANT.items():
            if 'model:'+m not in opts: errs.append(f'Model menu lacks {m}'); continue
            await pg.select_option('#lmod','model:'+m); await pg.wait_for_timeout(250)
            pts=await pg.evaluate("S.pts.map(p=>[p.r.chip,p.r.dev])"); mine=[d for c,d in pts if c==N1]; others={c for c,d in pts if c!=N1}
            print(f'  {m}: {len(mine)} N1X points, {len(others)} other chips')
            if sorted(mine)!=sorted(d for d,_ in v): errs.append(f'{m}: N1X points on the plot {mine}')
            if not others: errs.append(f'{m}: no other chip shares the plot')
        await pg.select_option('#lmod','other'); await pg.wait_for_timeout(250)
        k=await pg.evaluate(f"S.pts.filter(p=>p.r.chip==='{N1}').length"); print('Other metered runs, N1X points',k)
        if k!=8: errs.append(f'Other metered runs: {k} N1X points, expected 8 (7 from n1xllm.py and the MLPerf Client run)')
        # the matrix: no Llama 2 7B Q4_0 run, so the LLM cell stays an empty, documented gap
        await pg.goto(INDEX+'#all'); await pg.wait_for_timeout(600)
        cell=await pg.evaluate(f"(()=>{{const m=MROWS.find(m=>m.c==='{N1}');const x=m&&m.cells.find(x=>x.k==='llm');return x?x.td.textContent:null}})()"); print('matrix LLM cell',repr(cell))
        if cell!='–': errs.append(f'N1X matrix LLM cell is {cell!r}; if a Llama 2 7B Q4_0 run was added, drop the gap in mxfill_rows.json and this check')
        if 'llm|'+N1 not in gaps: errs.append('the N1X LLM gap is missing from mxfill_rows.json')
        pg2=await b.new_page(viewport={'width':390,'height':900}); pg2.on('pageerror',lambda e:errs.append('m '+str(e)))
        await pg2.goto(INDEX+'#llm'); await pg2.wait_for_timeout(500)
        sw=await pg2.evaluate("[document.documentElement.scrollWidth,document.body.scrollWidth]"); print('scrollWidth at 390',sw)
        if any(w>390 for w in sw): errs.append('horizontal overflow at 390px: '+str(sw))
        print('errors',errs); await b.close()
asyncio.run(main())
