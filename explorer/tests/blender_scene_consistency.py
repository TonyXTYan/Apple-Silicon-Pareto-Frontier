"""Blender scenes are consistent across machines: every machine (chip and device) with a three-scene Blender row has all three
scene rows (monster, junkshop, classroom) on that device (bl-cpu, bl-gpu), unless it is on the EXCEPTIONS list (the
`exceptions` of blscenes_rows.json), and its scenes add up to its three-scene point within 1% (3% for the five Apple rows in SUM_TOL), with the same power. On the
page, each scene view shows the same machines as the summed view (with every form shown and with the Server form hidden).
Also prints which points are on the CPU and GPU frontiers in each view."""
import asyncio, json, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
SCENES=('monster','junkshop','classroom')
EXCEPTIONS={}   # 'w|chip|dev' -> reason; must match blscenes_rows.json `exceptions`
# Apple rows (blender.py, unchanged here) whose scenes miss their three-scene point by more than 1%: that point is the published
# Open Data median of summed scores and the scene medians come from the snapshot, unscaled (README: within about 2%).
SUM_TOL={k:(0.03,'Apple: published three-scene median vs unscaled snapshot scene medians') for k in (
  'bl-cpu|M1|MacBook Air 13 (estimate)','bl-cpu|M1 Pro|MacBook Pro 16 (estimate)','bl-cpu|M2|Mac mini (estimate)','bl-cpu|M3|MacBook Pro 14 (estimate)',
  'bl-gpu|M2|MacBook Air 13 (8-core GPU) (estimate)')}
async def main():
    errs=[]
    rows_exc=json.load(open(HERE.parent/'blscenes_rows.json'))['exceptions']
    if rows_exc!=EXCEPTIONS: errs.append(f'exceptions in blscenes_rows.json {rows_exc} differ from this test')
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':1360,'height':1100})
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(INDEX+'#blender'); await pg.wait_for_timeout(500)
        # ---- data: every three-scene row has its three scenes, adding up within 1%, with the same power
        D=await pg.evaluate("ALL.filter(r=>r.w==='bl-cpu'||r.w==='bl-gpu').map(r=>({w:r.w,chip:r.chip,dev:r.dev,scene:r.scene||'',x:r.x,p:r.p,plo:r.plo,phi:r.phi,est:!!r.est,pe:!!r.pe,q:r.q,form:r.form,tier:r.tier,src:r.src}))")
        by={}
        for r in D: by.setdefault((r['w'],r['chip'],r['dev']),{}).setdefault(r['scene'],[]).append(r)
        nsum=0
        for k,v in sorted(by.items()):
            key='|'.join(k)
            if any(len(x)>1 for x in v.values()): errs.append(f'{key}: duplicate rows'); continue
            if '' not in v: errs.append(f'{key}: scene rows without a three-scene row'); continue
            nsum+=1; t=v[''][0]
            missing=[s for s in SCENES if s not in v]
            if missing:
                if key not in EXCEPTIONS: errs.append(f'{key}: no {",".join(missing)} scene row')
                continue
            if key in EXCEPTIONS: errs.append(f'{key}: listed as an exception but has its scenes')
            tot=sum(v[s][0]['x'] for s in SCENES)
            if abs(tot-t['x'])>SUM_TOL.get(key,(0.01,))[0]*t['x']: errs.append(f'{key}: scenes add up to {tot:.3f}, three-scene point is {t["x"]}')
            for s in SCENES:
                r=v[s][0]
                for f in ('p','plo','phi','est','pe','form','tier'):
                    if r[f]!=t[f]: errs.append(f'{key} {s}: {f} {r[f]!r} differs from the three-scene row ({t[f]!r})')
                if not t['tier'] in ('base','Pro','Max','Ultra') and (r['q']!=t['q'] or r['src']!=t['src']): errs.append(f'{key} {s}: q or src differs from the three-scene row')
        print('machines with a three-scene row:',nsum,'(CPU',sum(1 for k in by if k[0]=='bl-cpu'),', GPU',sum(1 for k in by if k[0]=='bl-gpu'),')')
        if nsum<73: errs.append(f'only {nsum} three-scene machines')
        # ---- page: each scene view shows the same machines as the summed view; frontier membership per view
        await pg.select_option('#base','')   # absolute axes, no baseline
        for label,hide in (('servers shown',False),('Server form hidden',True)):
            if hide:
                await pg.evaluate("S.forms.delete('server');all()"); await pg.wait_for_timeout(250)
            sets={}
            for sc in ('',)+SCENES:
                await pg.select_option('#lscene',sc); await pg.wait_for_timeout(250)
                r=await pg.evaluate("""()=>({m:S.pts.map(p=>p.r.w+'|'+p.r.chip+'|'+p.r.dev).sort(),srv:S.pts.filter(p=>p.r.form==='server').length,
                  f:Object.fromEntries(['bl-cpu','bl-gpu'].map(w=>[w,S.pts.filter(p=>p.front&&p.r.w===w).sort((a,b)=>a.r.x-b.r.x).map(p=>p.r.chip+' '+p.r.dev.replace(' (estimate)','')+' x='+p.r.x+' e='+p.r.e)]))})""")
                sets[sc]=r['m']
                print(f'{label}, {sc or "sum"}: {len(r["m"])} points, {r["srv"]} servers')
                for w in ('bl-cpu','bl-gpu'): print(f'   {w} frontier:',r['f'][w])
                if hide and r['srv']: errs.append(f'{label} {sc}: server points shown')
                if not hide and sc=='' and not r['srv']: errs.append('no server points in the summed view')
            for sc in SCENES:
                a,bb=set(sets['']),set(sets[sc])
                if a!=bb: errs.append(f'{label}: {sc} view differs from the summed view: only in sum {sorted(a-bb)[:4]}, only in {sc} {sorted(bb-a)[:4]}')
        print('errors',errs); await b.close()
asyncio.run(main())
