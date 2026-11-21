"""Blender tab: the Scene menu shows one scene (or the three-scene sum) for CPU and GPU, joined per chip; baselines compare the same scene and device."""
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
        await pg.goto(INDEX+'#blender'); await pg.wait_for_timeout(500)
        await pg.select_option('#base','M4 Max|')
        for sc in ['','monster','junkshop','classroom']:
            await pg.select_option('#lscene',sc); await pg.wait_for_timeout(250)
            r=await pg.evaluate("""()=>({n:S.pts.length,scenes:[...new Set(S.pts.map(p=>p.r.scene||''))],ws:[...new Set(S.pts.map(p=>p.r.w))].sort(),
              lines:document.querySelectorAll('#chart .pairl').length,weak:S.pts.filter(p=>weak(p.r)).length,rings:document.querySelectorAll('#chart .flag').length,
              bad:S.pts.filter(p=>{const v=relOf(p.r);return !v||v.b.w!==p.r.w||(v.b.scene||'')!==(p.r.scene||'')}).length,base:document.querySelectorAll('#chart .baseline-ring').length})""")
            print(sc or 'sum',r)
            if r['scenes']!=[sc]: errs.append('scene filter leaked '+sc)
            if r['ws']!=['bl-cpu','bl-gpu']: errs.append('missing a device '+sc)
            if r['lines']<15: errs.append('CPU-GPU lines missing '+sc)
            if r['bad']: errs.append('baseline from another scene or device '+sc)
            if r['base']!=2: errs.append('baseline should ring its CPU and GPU point '+sc)
            if r['weak']<5 or r['rings']!=r['weak']: errs.append('few-run medians not flagged '+sc)
        await pg.click('.tab[data-w="all"]'); await pg.wait_for_timeout(250)
        if await pg.evaluate("S.pts.some(p=>p.r.o&&p.r.o.scene)"): errs.append('scene rows leaked into All workloads')
        print('errors',errs); await b.close()
asyncio.run(main())
