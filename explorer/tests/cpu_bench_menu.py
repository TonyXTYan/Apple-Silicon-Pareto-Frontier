"""CPU tabs: the Benchmark choice isolates Cinebench 2024 (default, unchanged), Geekbench 6 and Cinebench 2026; every non-Cinebench-2024
point is speed measured / power estimated, Geekbench 5.5 conversions are hollow, baselines compare the same benchmark, and the
matrix and All workloads stay on Cinebench 2024."""
import asyncio, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
async def pick(pg,box,v):
    """choose v in a filter chip group as a user would: a single-choice row is clicked; a multi-select group is reset with Show all, then v alone is clicked ('' leaves every option on)"""
    if await pg.locator(f'#{box} [role=radio]').count(): await pg.click(f'#{box} [data-opt="{v}"]'); return
    if await pg.locator(f'#{box} .showall.on').count(): await pg.click(f'#{box} .showall')
    if v!='': await pg.click(f'#{box} [data-opt="{v}"]')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':1360,'height':1100}); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(INDEX); await pg.wait_for_timeout(400)
        await pg.evaluate("document.querySelector('.tab[data-w=\"llm\"]').click()"); await pg.wait_for_timeout(200)
        if not await pg.is_hidden('#lbmw'): errs.append('benchmark choice visible on the LLM tab')
        for tab in ('cpu-all','cpu-one'):
            await pg.click(f'.tab[data-w="{tab}"]'); await pg.wait_for_timeout(250)
            await pg.select_option('#base','')
            if not await pg.is_visible('#lbmw'): errs.append(tab+': benchmark choice hidden')
            n0=await pg.evaluate("S.pts.length")
            if await pg.evaluate("S.pts.some(p=>p.r.bm)"): errs.append(tab+': Cinebench 2024 view shows another benchmark')
            for bm,n in (('Geekbench 6',{'cpu-all':44,'cpu-one':43}[tab]),('Cinebench 2026',8),('Cinebench 2024',n0)):   # 32 Macs + 12/11 comparison machines; 5 Macs + 3
                await pick(pg,'lbmw',bm); await pg.select_option('#base','M4|Mac mini' if bm!='Cinebench 2026' else 'M5 Max|MacBook Pro 16'); await pg.wait_for_timeout(250)
                r=await pg.evaluate("""()=>({n:S.pts.length,bms:[...new Set(S.pts.map(p=>p.r.bm||'Cinebench 2024'))],pe:S.pts.every(p=>!p.r.bm||(p.r.pe&&p.r.plo&&/No wall power was published/.test(p.r.note))),
                  hollow:S.pts.filter(p=>p.r.bm&&p.r.resc).every(p=>p.g.querySelector('.mk.hollow')),nres:S.pts.filter(p=>p.r.bm&&p.r.resc).length,
                  bad:S.pts.filter(p=>{const v=relOf(p.r);return v&&(v.b.bm||'')!==(p.r.bm||'')}).length,k:G.k,x:WL[S.w].x})""")
                print(tab,bm,r)
                if r['n']!=n: errs.append(f'{tab} {bm}: {r["n"]} points, expected {n}')
                if r['bms']!=[bm]: errs.append(f'{tab} {bm}: benchmark filter leaked {r["bms"]}')
                if not r['pe'] or not r['hollow']: errs.append(f'{tab} {bm}: estimate or hollow marking wrong')
                if bm=='Geekbench 6' and r['nres']!=10: errs.append(f'{tab}: {r["nres"]} converted Geekbench 5.5 points, expected 10')
                if r['bad']: errs.append(f'{tab} {bm}: baseline from another benchmark')
                if r['k']==1: errs.append(f'{tab} {bm}: axis not relative to the baseline')
                if bm not in r['x']: errs.append(f'{tab} {bm}: axis title {r["x"]}')
        if await pg.evaluate("ALL.some(r=>r.bm&&mbest(r.ck,r.w)===r)"): errs.append('another benchmark leaked into the matrix')
        await pg.select_option('#base',''); await pg.click('.tab[data-w="all"]'); await pg.wait_for_timeout(250)
        if await pg.evaluate("S.pts.some(p=>p.r.o&&p.r.o.bm)"): errs.append('another benchmark leaked into All workloads')
        print('errors',errs); await b.close()
asyncio.run(main())
