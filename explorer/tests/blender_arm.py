"""Blender for the Arm comparison chips: the Snapdragon X Elite X1E-84-100 shows on the CPU in the three-scene view and in each
scene (one run, weaker-measurement grade, power borrowed so est+pe), with a baseline of the same scene; there is no Snapdragon
GPU point (no Cycles backend for Adreno) and no Ampere Blender point; the about text names both gaps."""
import asyncio, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
SD='Qualcomm Snapdragon X Elite X1E-84-100'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':1360,'height':1100}); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(INDEX+'#blender'); await pg.wait_for_timeout(500)
        sums={}
        for sc in ('','monster','junkshop','classroom'):
            await pg.select_option('#lscene',sc); await pg.wait_for_timeout(250)
            got=await pg.evaluate(f"S.pts.filter(p=>p.r.chip==={SD!r}).map(p=>[p.r.w,p.r.scene||'',p.r.q,!!p.r.est,!!p.r.pe,p.r.x,p.r.p])")
            print(sc or 'sum',got)
            if len(got)!=1 or got[0][0]!='bl-cpu' or got[0][1]!=sc: errs.append(f'{sc or "sum"}: expected one Snapdragon CPU point'); continue
            if got[0][2]!='B' or not got[0][3] or not got[0][4]: errs.append(f'{sc or "sum"}: Snapdragon point should be est+pe, grade B')
            sums[sc]=got[0]
            if await pg.evaluate("S.pts.some(p=>p.r.tier==='Ampere')"): errs.append(f'{sc or "sum"}: an Ampere Blender point appeared')
        if len(sums)==4:
            tot=sum(sums[s][5] for s in ('monster','junkshop','classroom'))
            if abs(tot-sums[''][5])>0.003: errs.append(f'scenes sum to {tot}, three-scene point is {sums[""][5]}')
            if len({v[6] for v in sums.values()})!=1: errs.append('scene rows should reuse the three-scene power')
        # baseline on the Snapdragon: every point (Snapdragon included) is compared with its point of the same scene and device
        opts=await pg.evaluate("[...document.querySelectorAll('#base option')].map(o=>o.value).filter(v=>v.startsWith('Qualcomm'))"); print('Qualcomm baselines',opts)
        if not opts: errs.append('no Qualcomm baseline option')
        else:
            await pg.select_option('#base',opts[0])
            for sc in ('','junkshop'):
                await pg.select_option('#lscene',sc); await pg.wait_for_timeout(250)
                r=await pg.evaluate(f"""()=>{{const v=S.pts.map(p=>[p,relOf(p.r)]);return {{cpu:v.filter(([p,x])=>x&&p.r.w==='bl-cpu').length,
                  bad:v.filter(([p,x])=>x&&(x.b.w!==p.r.w||(x.b.scene||'')!==(p.r.scene||''))).length,
                  self:v.filter(([p,x])=>p.r.chip==={SD!r}&&x&&x.b.chip==={SD!r}).length}}}}""")
                print('baseline',sc or 'sum',r)
                if r['bad'] or not r['cpu'] or r['self']!=1: errs.append(f'Snapdragon baseline wrong in {sc or "sum"}')
        g=await pg.evaluate("DATA.est.concat(DATA.rows).filter(r=>(r.w==='bl-gpu'&&r.tier==='Qualcomm')||(r.w.startsWith('bl')&&r.tier==='Ampere')).length")
        if g: errs.append('Snapdragon GPU or Ampere Blender rows exist')
        txt=await pg.evaluate("document.body.textContent")
        for k in ('no Adreno backend','Ampere has none'):
            if k not in txt: errs.append('about text missing: '+k)
        print('errors',errs); await b.close()
asyncio.run(main())
