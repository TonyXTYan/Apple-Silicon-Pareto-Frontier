"""M5 Ultra and M3 Ultra rows from ultra.py: the M5 Ultra Cinebench 2024 points (Notebookcheck speed, model efficiency, est+pe) replace
the model estimate on both CPU tabs and in the matrix row; the CPU Benchmark choice shows the M5 Ultra under Geekbench 6 (both tabs) and
Cinebench 2026 (all cores) and the M3 Ultra under Geekbench 6 (all cores); the M5 Ultra Blender CPU points carry the new borrowed power;
every new row says no wall power was published and cites a source URL."""
import asyncio, json, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
J=json.load(open(HERE.parent/'ultra_rows.json'))
CB={(c['w'],c['chip']):c['value'] for c in J['cinebench2024']}
BM={(c['w'],c['bm'],c['chip']):sum(c['runs'])/len(c['runs']) for c in J['cpubench']}
async def pick(pg,box,v):
    """choose v in a filter chip group as a user would: a single-choice row is clicked; a multi-select group is reset with Show all, then v alone is clicked ('' leaves every option on)"""
    if await pg.locator(f'#{box} [role=radio]').count(): await pg.click(f'#{box} [data-opt="{v}"]'); return
    if await pg.locator(f'#{box} .showall.on').count(): await pg.click(f'#{box} .showall')
    if v!='': await pg.click(f'#{box} [data-opt="{v}"]')
PT="""c=>S.pts.filter(p=>p.r.chip===c).map(p=>({x:p.r.x,p:p.r.p,est:!!p.r.est,pe:!!p.r.pe,src:p.r.src,bm:p.r.bm||'',dev:p.r.dev,
  note:/No wall power was published/.test(p.r.note||''),url:(SRC[p.r.src]||{}).url||''}))"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':1360,'height':1100}); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(INDEX); await pg.wait_for_timeout(400)
        if await pg.evaluate("ALL.some(r=>r.chip==='M5 Ultra'&&(r.w==='cpu-all'||r.w==='cpu-one')&&r.src==='model')"): errs.append('M5 Ultra model estimate still on a CPU tab')
        for tab in ('cpu-all','cpu-one'):
            await pg.click(f'.tab[data-w="{tab}"]'); await pg.wait_for_timeout(250); await pg.select_option('#base','')
            for bm in ('Cinebench 2024','Geekbench 6','Cinebench 2026'):
                await pick(pg,'lbmw',bm); await pg.wait_for_timeout(250)
                for chip in ('M5 Ultra','M3 Ultra'):
                    want=CB.get((tab,chip)) if bm=='Cinebench 2024' else BM.get((tab,bm,chip))
                    got=await pg.evaluate(PT,chip); print(tab,bm,chip,got and {k:v for k,v in got[0].items() if k!='url'})
                    if want is None:
                        if chip=='M3 Ultra' and bm=='Cinebench 2024':   # the review-speed model estimate (no pe) is unchanged, so hidden until estimates are shown
                            m3=await pg.evaluate(f"ALL.filter(r=>r.chip==='M3 Ultra'&&r.w==='{tab}'&&!r.bm).map(r=>r.src)")
                            if m3!=['model'] or got: errs.append(f'{tab}: M3 Ultra Cinebench 2024 estimate changed: {m3} {got}')
                        elif got: errs.append(f'{tab} {bm}: unexpected {chip} point')
                        continue
                    if len(got)!=1: errs.append(f'{tab} {bm}: {len(got)} {chip} points, expected 1'); continue
                    g=got[0]
                    if abs(g['x']-round(want,1))>0.051: errs.append(f'{tab} {bm} {chip}: x {g["x"]} expected {want}')
                    if not (g['est'] and g['pe'] and g['note'] and g['url'].startswith('https://')): errs.append(f'{tab} {bm} {chip}: should be est+pe with a cited source, got {g}')
                    if g['dev']!='Mac Studio': errs.append(f'{tab} {bm} {chip}: machine {g["dev"]}')
        # matrix row: the M5 Ultra CPU cells are the new rows (dashed estimates, ~), Blender CPU carries the new power
        # a chip with no wall reading at all (the M5 Ultra) has a matrix row only with estimates shown, as before this step
        await pg.click('.tab[data-w="all"]'); await pg.wait_for_timeout(300)
        if await pg.evaluate("MROWS.some(m=>m.c==='M5 Ultra')"): errs.append('M5 Ultra matrix row shown with estimates off')
        await pg.evaluate("(()=>{const e=document.getElementById('est');if(!e.checked)e.click()})()"); await pg.wait_for_timeout(300)
        m=await pg.evaluate("""(()=>{const m=MROWS.find(m=>m.c==='M5 Ultra');return m?m.cells.map(x=>({k:x.k,t:x.td.textContent,src:x.r&&x.r.src,p:x.r&&x.r.p,x:x.r&&x.r.x,cls:x.td.classList.contains('isest')})):null})()""")
        print('matrix M5 Ultra',m)
        if not m: errs.append('no M5 Ultra matrix row')
        else:
            mm={c['k']:c for c in m}
            for k in ('cpu-all','cpu-one'):
                c=mm.get(k)
                if not c or c['src']!='nbc_m5u' or c['x']!=CB[(k,'M5 Ultra')] or not c['t'].startswith('~') or not c['cls']: errs.append(f'matrix M5 Ultra {k}: {c}')
            cp=await pg.evaluate("ALL.find(r=>r.chip==='M5 Ultra'&&r.w==='cpu-all'&&!r.bm).p")
            if not mm.get('bl-cpu') or mm['bl-cpu']['p']!=cp: errs.append(f"matrix M5 Ultra Blender CPU power {mm.get('bl-cpu')} should be the Cinebench power {cp}")
        m3=await pg.evaluate("(()=>{const m=MROWS.find(m=>m.c==='M3 Ultra');const x=m&&m.cells.find(x=>x.k==='cpu-all');return x&&x.r?x.r.src:null})()")
        if m3!='model': errs.append(f'matrix M3 Ultra CPU cell should stay the Cinebench 2024 estimate, got {m3}')
        # Blender tab, CPU device: the M5 Ultra points (three-scene and each scene) carry the new power
        await pg.click('.tab[data-w="blender"]'); await pg.wait_for_timeout(200); await pick(pg,'ldevw','bl-cpu'); await pg.wait_for_timeout(300)
        cp=await pg.evaluate("ALL.find(r=>r.chip==='M5 Ultra'&&r.w==='cpu-all'&&!r.bm).p")
        bl=await pg.evaluate(PT,'M5 Ultra'); print('Blender CPU M5 Ultra',[(g['x'],g['p']) for g in bl])
        if not bl or any(g['p']!=cp for g in bl): errs.append(f'Blender CPU M5 Ultra power {bl}')
        print('errors',errs); await b.close()
asyncio.run(main())
