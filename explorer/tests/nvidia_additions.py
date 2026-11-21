"""NVIDIA additions and comparison-chip gaps: the N1X (RTX Spark) is a comparison chip of its own (NVIDIA colour, laptops,
Cinebench, Cyberpunk and an estimated LLM point) and works as a baseline; new GB10, DGX Spark, RTX 4060, RTX 5090 and RTX 4090
rows are present with whole-machine power; the matrix marks cells that cannot exist as n/a, styled apart from – (not measured)."""
import asyncio, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
N1='NVIDIA N1X (RTX Spark)'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':1360,'height':1100}); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(INDEX); await pg.wait_for_timeout(400)
        n1=await pg.evaluate(f"ALL.filter(r=>r.chip==='{N1}'&&!r.bm).map(r=>[r.w,r.tier,r.form,r.gen,!!r.pe,r.q])"); print('N1X rows',n1)
        nb=await pg.evaluate(f"ALL.filter(r=>r.chip==='{N1}'&&r.bm).map(r=>r.w+' '+r.bm).sort()"); print('N1X Benchmark-menu rows',nb)   # cpubench2.py: Geekbench 6 and Cinebench 2026, two laptops x two CPU tabs
        if nb!=sorted([w+' '+bm for w in ('cpu-all','cpu-one') for bm in ('Cinebench 2026','Geekbench 6') for _ in (0,1)]): errs.append('N1X Benchmark-menu rows wrong')
        if sorted(r[0] for r in n1)!=['bl-cpu','bl-gpu','cpu-all','cpu-all','cpu-one','cpu-one','gpu','gpu']+['llm']*8 or any(r[1]!='NVIDIA' or r[2]!='laptop' or r[3]!=0 for r in n1): errs.append('N1X rows wrong')   # bl-cpu and bl-gpu from mxfill.py, seven of the llm rows from n1xllm.py
        if not await pg.evaluate("ALL.some(r=>r.chip==='NVIDIA GB10'&&r.model==='Llama 3.3 70B'&&!r.est&&r.p===156)"): errs.append('GB10 Llama 3.3 70B row missing')
        sp=await pg.evaluate("ALL.filter(r=>r.dev==='NVIDIA DGX Spark').map(r=>[r.model,r.p,r.plo,r.phi,!!r.pe])"); print('DGX Spark',sp)
        if len(sp)!=5 or any(not (s[4] and s[1]==160 and s[2]==120 and s[3]==206) for s in sp): errs.append('DGX Spark rows')
        if await pg.evaluate("ALL.some(r=>/ThinkPad P1/.test(r.dev))"): errs.append('flagged ThinkPad P1 Gen 7 should be left out')
        for c,n in (('NVIDIA GeForce RTX 4060 Laptop',6),('NVIDIA GeForce RTX 4060',2),('NVIDIA GeForce RTX 5090',3),('NVIDIA GeForce RTX 5090 Laptop',6)):   # mxfill.py adds Blender GPU and Llama 2 7B rows
            k=await pg.evaluate(f"ALL.filter(r=>r.chip==='{c}').length")
            if k!=n: errs.append(f'{c}: {k} rows, expected {n}')
        # baseline: an N1X laptop on the CPU and gaming tabs
        await pg.click('.tab[data-w="cpu-all"]'); await pg.select_option('#base',N1+'|Asus ProArt P16 H7607 (RTX Spark)'); await pg.wait_for_timeout(300)
        r=await pg.evaluate("({tb:tabBase(curBase()).map(r=>r.dev),ring:document.querySelectorAll('#chart .baseline-ring').length,col:getComputedStyle(document.querySelector('#chart g.m.t-NVIDIA .mk')).fill,n:S.pts.filter(p=>p.r.chip==='"+N1+"').length})"); print('cpu-all vs N1X ProArt',r)
        if r['tb']!=['Asus ProArt P16 H7607 (RTX Spark)'] or r['ring']!=1 or r['n']!=2: errs.append('N1X baseline on cpu-all')
        await pg.click('.tab[data-w="gpu"]'); await pg.wait_for_timeout(300)
        g=await pg.evaluate("baseRow('gpu',curBase(),'Cyberpunk 2077').dev"); print('gaming baseline row',g)
        if g!='Asus ProArt P16 H7607 (RTX Spark)': errs.append('N1X baseline on gaming')
        # Blender: the 155H iGPU joins its CPU point; the Snapdragon and GB10 CPU points are there
        await pg.click('.tab[data-w="blender"]'); await pg.wait_for_timeout(300)
        bl=await pg.evaluate("({g155:S.pts.filter(p=>p.r.grp==='Intel Core Ultra 7 155H|bl').length,xe:S.pts.some(p=>p.r.chip.startsWith('Qualcomm')&&p.r.w==='bl-cpu'),gb:S.pts.some(p=>p.r.chip==='NVIDIA GB10'&&p.r.w==='bl-cpu'&&weak(p.r))})"); print('blender',bl)
        if bl!={'g155':2,'xe':True,'gb':True}: errs.append('Blender additions')
        # matrix: n/a cells
        m=await pg.evaluate("""()=>{const out={};for(const m of MROWS){out[m.c]=m.cells.map(x=>x.td.textContent+(x.td.classList.contains('nap')?'#':''))}
          const nap=document.querySelector('#matrix td.nap'),na=document.querySelector('#matrix td.na');
          return {rows:out,napTitle:nap&&nap.title,napBg:nap&&getComputedStyle(nap).backgroundImage,naBg:na&&getComputedStyle(na).backgroundImage,key:document.getElementById('mkey').textContent}}""")
        rows=m['rows']
        for c,ks in (('NVIDIA GeForce RTX 4060',[0,1,2,3]),('NVIDIA GeForce RTX 5090 Laptop',[0,1,2,3]),('NVIDIA GB10',[0,1,4]),('Qualcomm Snapdragon X Elite X1E-84-100',[5])):
            got=[i for i,v in enumerate(rows.get(c,[])) if v=='n/a#']; print('n/a',c,got)
            if got!=ks: errs.append(f'n/a cells for {c}: {got}, expected {ks}')
        if rows.get('NVIDIA GB10',[''])[3] in ('–','n/a#'): errs.append('GB10 Blender CPU should have a value')
        if any(v=='n/a#' for c,vs in rows.items() if not c.startswith(('NVIDIA','Qualcomm')) for v in vs): errs.append('n/a on a chip without a rule')
        print('n/a title',m['napTitle']); print('backgrounds',m['napBg'][:40],'|',m['naBg'])
        if not m['napTitle'] or not m['napTitle'].startswith('Cannot exist') or m['napBg']=='none' or m['naBg']!='none': errs.append('n/a cells not styled apart or lack a reason')
        if 'n/a' not in m['key']: errs.append('matrix key does not explain n/a')
        pg2=await b.new_page(viewport={'width':390,'height':900}); pg2.on('pageerror',lambda e:errs.append('m '+str(e)))
        await pg2.goto(INDEX+'#gpu'); await pg2.wait_for_timeout(400)
        sw=await pg2.evaluate("document.documentElement.scrollWidth")
        if sw>390: errs.append(f'scrollWidth {sw} at 390px')
        print('errors',errs); await b.close()
asyncio.run(main())
