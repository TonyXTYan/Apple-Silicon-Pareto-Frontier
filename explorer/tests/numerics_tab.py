"""Numerical libraries tab: the Set menu isolates each set, OpenBLAS and Accelerate are joined per chip, baselines compare the same set and library, and the tab stays out of All workloads and the matrix."""
import asyncio, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':1360,'height':1100}); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(INDEX); await pg.wait_for_timeout(400)
        await pg.click('.tab[data-w="blas"]'); await pg.wait_for_timeout(300)
        print('set menu visible',await pg.is_visible('#lset'),'default',await pg.evaluate("S.lset"))
        await pg.select_option('#base','M4|')
        for st,n,lines in (('julia-sgemm',20,10),('arxiv-sgemm',8,4),('julia-dgemm',3,0),('',31,14)):
            await pg.select_option('#lset',st); await pg.wait_for_timeout(250)
            r=await pg.evaluate("""()=>({n:S.pts.length,sets:[...new Set(S.pts.map(p=>p.r.set))],pe:S.pts.every(p=>p.r.pe&&p.r.plo&&/No wall power was metered/.test(p.r.note)),
              lines:document.querySelectorAll('#chart path[style*="stroke-width:1.4"]').length,
              bad:S.pts.filter(p=>{const v=relOf(p.r);return v&&(v.b.set!==p.r.set||v.b.lib!==p.r.lib)}).length,rel:S.pts.filter(p=>relOf(p.r)).length})""")
            print(st or 'every',r)
            if r['n']!=n: errs.append(f'{st}: {r["n"]} points, expected {n}')
            if st and r['sets']!=[st]: errs.append('set filter leaked '+st)
            if r['lines']!=lines: errs.append(f'{st}: {r["lines"]} pair lines, expected {lines}')
            if not r['pe']: errs.append(st+': a point is not marked speed measured, power estimated')
            if r['bad']: errs.append(st+': baseline from another set or library')
        if not await pg.evaluate("S.pts.some(p=>relOf(p.r))"): errs.append('no like-for-like baseline found for M4')
        await pg.click('.tab[data-w="all"]'); await pg.wait_for_timeout(250)
        if await pg.evaluate("S.pts.some(p=>p.r.ow==='blas')"): errs.append('numerics leaked into All workloads')
        if await pg.evaluate("[...document.querySelectorAll('#matrix thead th')].some(t=>/Numerical/.test(t.textContent))"): errs.append('numerics leaked into the matrix')
        print('errors',errs); await b.close()
asyncio.run(main())
