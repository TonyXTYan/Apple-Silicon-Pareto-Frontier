"""The Speed vs power button swaps the chart to speed (y) against wall power (x), points slide there, the frontier
runs toward the top left, and switching back restores the default; disabled on All workloads."""
import asyncio, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
CHECK="""()=>{const {X,Y}=G;let bad=0;for(const p of S.pts){const r=p.r;if(Math.abs(p.px-X(G.PV?r.p:r.x))>.5||Math.abs(p.py-Y(G.PV?r.x:r.e*G.kr(r)))>.5)bad++}
  /* PV frontier: no point in the same group has less (or equal) power and more speed */
  let dom=0;if(G.PV)for(const p of S.pts.filter(p=>p.front))for(const q of S.pts){if(q===p||q.r.w!==p.r.w||String(vk(q.r)||'').replace(' (oMLX)','')!==String(vk(p.r)||'').replace(' (oMLX)',''))continue;
    if((!S.fest&&(q.r.est||q.r.pe)))continue;if(q.r.p<=p.r.p&&q.r.x>p.r.x*1.000001)dom++}
  return {pv:G.PV,bad,dom,front:S.pts.filter(p=>p.front).length,xt:document.querySelector('#chart .axt').textContent,sw:document.documentElement.scrollWidth}}"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox']); errs=[]
        for vw in (1360,390):
            pg=await b.new_page(viewport={'width':vw,'height':1000}); pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.goto(INDEX); await pg.wait_for_timeout(500); await pg.evaluate("document.getElementById('front').click()")
            for w in ('llm','cpu-all','blender','gpu','hpl'):
                await pg.evaluate(f"document.querySelector('.tab[data-w=\"{w}\"]').click()"); await pg.wait_for_timeout(150)
                if not await pg.evaluate("G.PV"): await pg.click('#pvb')
                await pg.wait_for_timeout(1000); r=await pg.evaluate(CHECK); print(vw,w,r)
                if not r['pv'] or r['bad'] or r['dom'] or not r['front'] or 'power' not in r['xt'].lower(): errs.append(f'{vw} {w} {r}')
                if r['sw']>vw: errs.append(f'{vw} {w} overflow {r["sw"]}')
                tr=await pg.evaluate("S.pts.filter(p=>p.g&&p.g.style.transform).length")
                if tr: errs.append(f'{vw} {w} {tr} points still transformed after the slide')
            await pg.click('#pvb'); await pg.wait_for_timeout(1000); r=await pg.evaluate(CHECK); print(vw,'back',r)
            if r['pv'] or r['bad']: errs.append(f'{vw} back {r}')
            await pg.click('#pvb'); await pg.wait_for_timeout(200)
            await pg.evaluate("document.querySelector('.tab[data-w=\"all\"]').click()"); await pg.wait_for_timeout(200)
            d=await pg.evaluate("[document.getElementById('pvb').disabled,G.PV]"); print(vw,'all',d)
            if d!=[True,False]: errs.append(f'all tab {d}')
        print('errors',errs); await b.close()
asyncio.run(main())
