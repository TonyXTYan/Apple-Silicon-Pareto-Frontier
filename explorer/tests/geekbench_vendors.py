"""CPU tabs, Benchmark choice: Geekbench 6 (and Cinebench 2026) points for the comparison vendors (cpubench2.py). Choosing
Geekbench 6 on CPU all-cores and one-thread shows Intel, AMD, Qualcomm and NVIDIA points, all speed measured / power estimated
and none hollow; Cinebench 2026 shows the Intel and NVIDIA machines; a comparison-machine baseline compares like with like;
and at 390px there is no horizontal overflow."""
import asyncio, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
V={'Intel','AMD','Qualcomm','NVIDIA'}
async def pick(pg,box,v):
    """choose v in a filter chip group as a user would: a single-choice row is clicked; a multi-select group is reset with Show all, then v alone is clicked ('' leaves every option on)"""
    if await pg.locator(f'#{box} [role=radio]').count(): await pg.click(f'#{box} [data-opt="{v}"]'); return
    if await pg.locator(f'#{box} .showall.on').count(): await pg.click(f'#{box} .showall')
    if v!='': await pg.click(f'#{box} [data-opt="{v}"]')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
        errs=[]
        for vw in (1360,390):
            pg=await b.new_page(viewport={'width':vw,'height':1100}); pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.goto(INDEX); await pg.wait_for_timeout(400)
            for tab,ng in (('cpu-all',12),('cpu-one',11)):
                await pg.click(f'.tab[data-w="{tab}"]'); await pg.wait_for_timeout(250)
                await pg.select_option('#base',''); await pick(pg,'lbmw','Geekbench 6'); await pg.wait_for_timeout(250)
                r=await pg.evaluate("""()=>{const c=S.pts.filter(p=>!['base','Pro','Max','Ultra'].includes(p.r.tier));
                  return {tiers:[...new Set(c.map(p=>p.r.tier))],n:c.length,pe:c.every(p=>p.r.pe&&p.r.q==='E'&&/No wall power was published/.test(p.r.note)),
                    hollow:c.filter(p=>p.g.querySelector('.mk.hollow')).length,bms:[...new Set(S.pts.map(p=>p.r.bm))],
                    ow:document.documentElement.scrollWidth-document.documentElement.clientWidth}}""")
                print(vw,tab,'Geekbench 6',r)
                if not V<=set(r['tiers']): errs.append(f'{vw} {tab}: Geekbench 6 vendors shown {r["tiers"]}')
                if r['n']!=ng: errs.append(f'{vw} {tab}: {r["n"]} comparison Geekbench points, expected {ng}')
                if not r['pe'] or r['hollow']: errs.append(f'{vw} {tab}: comparison points not estimate-marked or drawn hollow')
                if r['bms']!=['Geekbench 6']: errs.append(f'{vw} {tab}: benchmark filter leaked {r["bms"]}')
                if r['ow']>0: errs.append(f'{vw} {tab}: horizontal overflow {r["ow"]}px')
                await pick(pg,'lbmw','Cinebench 2026'); await pg.wait_for_timeout(250)
                t=await pg.evaluate("[...new Set(S.pts.filter(p=>!['base','Pro','Max','Ultra'].includes(p.r.tier)).map(p=>p.r.tier))].sort()")
                print(vw,tab,'Cinebench 2026 vendors',t)
                if t!=['Intel','NVIDIA']: errs.append(f'{vw} {tab}: Cinebench 2026 vendors {t}')
                if vw==1360:
                    await pick(pg,'lbmw','Geekbench 6'); await pg.select_option('#base','AMD Ryzen AI Max+ 395|Asus ROG Flow Z13 (2025)'); await pg.wait_for_timeout(250)
                    q=await pg.evaluate("""()=>({k:G.k,bad:S.pts.filter(p=>{const v=relOf(p.r);return v&&(v.b.bm||'')!==(p.r.bm||'')}).length,
                       ring:document.querySelectorAll('#chart .baseline-ring').length})""")
                    print(vw,tab,'vs Z13',q)
                    if q['k']==1 or q['bad'] or q['ring']!=1: errs.append(f'{tab}: Z13 Geekbench baseline wrong {q}')
                await pick(pg,'lbmw','Cinebench 2024'); await pg.wait_for_timeout(200)
                if await pg.evaluate("S.pts.some(p=>p.r.bm)"): errs.append(f'{vw} {tab}: Cinebench 2024 view shows another benchmark')
            await pg.close()
        print('errors',errs); await b.close()
asyncio.run(main())
