"""Linear algebra tab (HPL and the GEMM sets merged): the Set menu opens on HPL, isolates each set, OpenBLAS and Accelerate are
joined per chip, frontiers are drawn per set and library, baselines compare the same set and library, old #hpl and #blas links
open the right set, and only HPL reaches All workloads and the matrix."""
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
        tabs=await pg.evaluate("[...document.querySelectorAll('.tab')].map(t=>t.dataset.w)")
        if 'blas' in tabs or 'hpl' not in tabs: errs.append('tabs not merged: '+','.join(tabs))
        sub=await pg.evaluate("document.querySelector('.tab[data-w=\"hpl\"] small').textContent"); print('tab sub-label',sub)
        if 'GEMM' not in sub or 'HPL' not in sub: errs.append('tab sub-label')
        await pg.click('.tab[data-w="hpl"]'); await pg.wait_for_timeout(300)
        print('set menu visible',await pg.is_visible('#lset'),'default',await pg.evaluate("S.lset"))
        if await pg.evaluate("S.lset")!='hpl': errs.append('Linear algebra should open on HPL')
        nh=await pg.evaluate("ALL.filter(r=>r.w==='hpl'&&(!r.est||r.pe)).length")
        await pg.select_option('#base','M4|')
        for st,n,lines in (('hpl',nh,0),('julia-sgemm',20,10),('arxiv-sgemm',8,4),('julia-dgemm',3,0),('',31+nh,14)):
            await pg.select_option('#lset',st); await pg.wait_for_timeout(250)
            r=await pg.evaluate("""()=>({n:S.pts.length,sets:[...new Set(S.pts.map(p=>p.r.set||p.r.w))],pe:S.pts.filter(p=>p.r.w==='blas').every(p=>p.r.pe&&p.r.plo&&/No wall power was metered/.test(p.r.note)),
              vend:S.pts.some(p=>p.r.w==='hpl'&&p.r.gen===0),solid:S.pts.filter(p=>p.r.w==='hpl'&&!p.r.est&&!p.r.sys).every(p=>kindOf(p.r)==='solid'),
              lines:document.querySelectorAll('#chart path[style*="stroke-width:1.4"]').length,abs:!axisRel(),
              bad:S.pts.filter(p=>{const v=relOf(p.r);return v&&(v.b.w!==p.r.w||v.b.set!==p.r.set||v.b.lib!==p.r.lib)}).length,rel:S.pts.filter(p=>relOf(p.r)).length,
              ring:document.querySelectorAll('#chart .baseline-ring').length,x:document.querySelector('#chart .axt').textContent})""")
            print(st or 'every',r)
            if r['n']!=n: errs.append(f'{st}: {r["n"]} points, expected {n}')
            if st and r['sets']!=[st]: errs.append('set filter leaked '+st)
            if r['lines']!=lines: errs.append(f'{st}: {r["lines"]} pair lines, expected {lines}')
            if not r['pe']: errs.append(st+': a GEMM point is not marked speed measured, power estimated')
            if r['bad']: errs.append(st+': baseline from another set or library')
            if st!='julia-dgemm' and not r['ring']: errs.append(st+': no baseline ring')
            if st=='julia-dgemm' and 'Not shown against M4: this GEMM set' not in await pg.evaluate("document.getElementById('wnote').textContent"): errs.append('no missing-baseline note for DGEMM')
            if st=='hpl' and (not r['vend'] or not r['solid'] or r['abs']): errs.append('HPL set: comparison machines, solid points or ratio axis missing')
            if st and st!='hpl' and not r['abs']: errs.append(st+': GEMM sets should keep absolute axes')
        # every set: one frontier per set and library, each named
        await pg.select_option('#base',''); await pg.check('#front'); await pg.wait_for_timeout(250)
        fl=await pg.evaluate("[...document.querySelectorAll('#chart .flab')].map(t=>t.textContent)"); print('frontier names (every set)',fl)
        if 'HPL' not in fl or not any('Accelerate' in t for t in fl): errs.append('every-set frontier names missing')
        await pg.uncheck('#front')
        await pg.click('.tab[data-w="all"]'); await pg.wait_for_timeout(250)
        if await pg.evaluate("S.pts.some(p=>p.r.ow==='blas')"): errs.append('GEMM sets leaked into All workloads')
        if not await pg.evaluate("S.pts.some(p=>p.r.ow==='hpl')"): errs.append('HPL missing from All workloads')
        hd=await pg.evaluate("[...document.querySelectorAll('#matrix thead th')].map(t=>t.textContent)")
        if hd.count('Linear algebra')!=1 or any('GEMM' in t or 'Numerical' in t for t in hd): errs.append('matrix columns changed: '+'|'.join(hd))
        for h,w,s in (('#hpl','hpl','hpl'),('#blas','hpl','julia-sgemm')):
            pg2=await b.new_page(viewport={'width':390,'height':900}); pg2.on('pageerror',lambda e:errs.append('m '+str(e)))
            await pg2.goto(INDEX+h); await pg2.wait_for_timeout(400)
            got=await pg2.evaluate("S.w+' '+S.lset+' '+document.querySelector('.tab[aria-selected=true]').dataset.w"); print('old link',h,'opens',got)
            if got!=f'{w} {s} {w}': errs.append('old link '+h+' opens '+got)
            sw=await pg2.evaluate("document.documentElement.scrollWidth")
            if sw>390: errs.append(f'{h}: scrollWidth {sw} at 390px')
            await pg2.close()
        print('errors',errs); await b.close()
asyncio.run(main())
