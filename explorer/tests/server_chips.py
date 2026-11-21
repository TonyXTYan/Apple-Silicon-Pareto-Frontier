"""Server-class CPUs: the Server machine-form chip (hexagon) highlights on hover and solo-filters on click with the fading
Show all; Ampere is a vendor tier with its own colour in light and dark; SPECpower_ssj2008 is a server-only entry of the CPU
all-cores Benchmark menu that renders its points against a server baseline (and restores the default baseline when left);
Green500 rows are flagged as system-level; server rows stay out of the matrix and All workloads; no horizontal overflow at 390px."""
import asyncio, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
SPEC='SPECpower_ssj2008'
TOK="['--s-intel','--s-amd','--s-qcom','--s-nv','--s-base','--s-pro','--s-max','--s-ultra','--s-amp'].map(k=>getComputedStyle(document.documentElement).getPropertyValue(k).trim())"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
        errs=[]; cols={}
        for scheme in ('dark','light'):
            pg=await b.new_page(viewport={'width':1360,'height':1100},color_scheme=scheme); pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.goto(INDEX); await pg.wait_for_timeout(400); cols[scheme]=await pg.evaluate(TOK)
            if scheme=='light': break
            await pg.close()
        print('tokens light',cols['light'][-1],'dark',cols['dark'][-1])
        for s in ('light','dark'):
            if len(set(cols[s]))!=9 or '' in cols[s]: errs.append(s+': Ampere colour missing or repeats another tier')
        if cols['light'][-1]==cols['dark'][-1]: errs.append('Ampere dark token not stepped')
        # defaults unchanged
        st=await pg.evaluate("S.w+' '+JSON.stringify(S.base)"); print('opens on',st)
        if st!='cpu-all null': errs.append('default view changed')
        await pg.evaluate("document.querySelector('.tab[data-w=\"llm\"]').click()"); await pg.wait_for_timeout(200)
        # Ampere tier chip and its colour on the plot (LLM: the AmpereOne DeepSeek R1 671B run)
        chips=await pg.evaluate("[...document.querySelectorAll('#tiers .chip')].map(c=>c.textContent.trim())")
        if 'Ampere' not in chips: errs.append('Ampere tier chip missing')
        r=await pg.evaluate("""()=>{const q=S.pts.find(p=>p.r.tier==='Ampere');if(!q)return null;const m=q.g.querySelector('.mk');return {model:q.r.model,p:q.r.p,fill:getComputedStyle(m).fill,form:q.r.form}}""")
        print('LLM Ampere point',r)
        if not r or r['model']!='DeepSeek R1 671B' or r['p']!=477 or r['form']!='server': errs.append('AmpereOne LLM row missing or wrong')
        else:
            want=await pg.evaluate("(()=>{const d=document.createElement('div');d.style.color=getComputedStyle(document.documentElement).getPropertyValue('--s-amp');document.body.appendChild(d);const c=getComputedStyle(d).color;d.remove();return c})()")
            if r['fill']!=want: errs.append(f'Ampere point not drawn in the Ampere colour: {r["fill"]} vs {want}')
        # Server form chip: exists with a hexagon, hover highlights, click solos, Show all fades in and restores
        await pg.click('.tab[data-w="hpl"]'); await pg.wait_for_timeout(300)
        f=await pg.evaluate("""()=>{const b=document.querySelector('#forms [data-opt="server"]');return b?{t:b.textContent.trim(),path:(b.querySelector('svg path')||{}).getAttribute?.('d')||'',n:(b.querySelector('svg path').getAttribute('d').match(/L/g)||[]).length}:null}""")
        print('server chip',f)
        if not f or f['t']!='Server' or f['n']!=5: errs.append('Server form chip missing or not a hexagon')
        n0=await pg.evaluate("S.pts.length"); ns=await pg.evaluate("S.pts.filter(p=>p.r.form==='server').length")
        await pg.hover('#forms [data-opt="server"]'); await pg.wait_for_timeout(150)
        h=await pg.evaluate("({hl:S.hl,dim:S.pts.filter(p=>p.g.classList.contains('dim')).length,srvdim:S.pts.filter(p=>p.r.form==='server'&&p.g.classList.contains('dim')).length})"); print('hover',h,'of',n0)
        if not h['hl'] or h['hl'].get('v')!='server' or h['dim']!=n0-ns or h['srvdim']: errs.append('Server chip hover highlight broken')
        await pg.mouse.move(5,5); await pg.click('#forms [data-opt="server"]'); await pg.wait_for_timeout(250)
        r=await pg.evaluate("({n:S.pts.length,forms:[...new Set(S.pts.map(p=>p.r.form))],sa:document.querySelector('#forms .showall').classList.contains('on'),press:[...document.querySelectorAll('#forms [data-opt]')].map(b=>b.dataset.opt+':'+b.getAttribute('aria-pressed'))})"); print('solo',r)
        if r['forms']!=['server'] or r['n']!=ns or not r['sa']: errs.append('Server chip solo or Show all broken')
        op=await pg.evaluate("getComputedStyle(document.querySelector('#forms .showall')).opacity")
        await pg.click('#forms .showall'); await pg.wait_for_timeout(250)
        r=await pg.evaluate("({n:S.pts.length,sa:document.querySelector('#forms .showall').classList.contains('on')})"); print('show all',r,'opacity while soloed',op)
        if r['n']!=n0 or r['sa'] or float(op)<0.5: errs.append('Show all did not restore every form or was not visible')
        # Green500 rows: hollow, weaker ring, system-level in the note, tooltip and table
        g=await pg.evaluate("""()=>{const q=S.pts.filter(p=>p.r.sys);return {n:q.length,hollow:q.every(p=>p.g.querySelector('.mk.hollow')),ring:q.every(p=>p.g.querySelector('.flag')),weak:q.every(p=>weak(p.r)),
          note:q.every(p=>/System-level power/.test(p.r.note)&&/upper bound/.test(p.r.note)),srv:q.every(p=>p.r.form==='server'&&p.r.srv),geer:S.pts.filter(p=>p.r.tier==='Ampere').length}}""")
        print('green500',g)
        if g['n']!=11 or not (g['hollow'] and g['ring'] and g['weak'] and g['note'] and g['srv']): errs.append('Green500 rows not flagged as system-level')
        if g['geer']!=6: errs.append(f'expected 6 Geerling Ampere HPL rows, got {g["geer"]}')
        await pg.evaluate("(()=>{const q=S.pts.find(p=>p.r.sys);showTip(q,'hover')})()")
        tip=await pg.evaluate("document.getElementById('tip').textContent")
        if 'system-level power' not in tip: errs.append('Green500 tooltip does not say system-level')
        await pg.evaluate("document.getElementById('numbers').open=true"); await pg.wait_for_timeout(150)
        if not await pg.evaluate("[...document.querySelectorAll('#table .pill')].some(s=>s.textContent==='system-level power')"): errs.append('table pill for system-level rows missing')
        if 'system-level' not in await pg.evaluate("document.getElementById('legend').textContent"): errs.append('legend lacks the system-level entry')
        # SPECpower: server-only Benchmark entry, rendered points, server baseline, restored on the way out
        await pg.click('.tab[data-w="cpu-all"]'); await pg.wait_for_timeout(250)
        await pg.select_option('#lbm',SPEC); await pg.wait_for_timeout(300)
        r=await pg.evaluate("""()=>({n:S.pts.length,bms:[...new Set(S.pts.map(p=>p.r.bm))],forms:[...new Set(S.pts.map(p=>p.r.form))],meas:S.pts.every(p=>!p.r.est&&p.r.q==='A'),
          drawn:document.querySelectorAll('#chart g.m .mk').length,b:JSON.stringify(S.base),tb:tabBase(curBase()).map(r=>r.dev),k:G.k,x:WL[S.w].x,eu:WL[S.w].eu,
          bad:S.pts.filter(p=>{const v=relOf(p.r);return !v||v.b.bm!==p.r.bm}).length,ring:document.querySelectorAll('#chart .baseline-ring').length,
          finding:document.getElementById('finding').textContent,legend:document.getElementById('legend').textContent})""")
        print('SPECpower',{k:v for k,v in r.items() if k not in ('finding','legend')})
        if r['n']!=26 or r['drawn']!=26 or r['bms']!=[SPEC] or r['forms']!=['server'] or not r['meas']: errs.append('SPECpower points not rendered as 26 measured server points')
        if r['b']!='{"chip":"AMD EPYC 9654","dev":"Lenovo ThinkSystem SR655 V3"}' or r['tb']!=['Lenovo ThinkSystem SR655 V3'] or r['k']==1 or r['bad'] or r['ring']!=1: errs.append('SPECpower server baseline not applied')
        if 'ssj_ops' not in r['x'] or r['eu']!='k ssj_ops/J' or 'Servers only' not in r['finding'] or SPEC not in r['legend']: errs.append('SPECpower axis, finding or legend wrong')
        mu=await pg.evaluate("[...document.querySelectorAll('#matrix td.cell')].some(td=>/ssj/.test(td.textContent+td.title))")
        if mu: errs.append('matrix picked up SPECpower units')
        await pg.select_option('#base','M4 Max|MacBook Pro 14'); await pg.wait_for_timeout(250)
        r=await pg.evaluate("({k:G.k,n:S.pts.length,x:document.getElementById('basex').textContent,note:document.getElementById('wnote').textContent})"); print('SPECpower vs a Mac',r['k'],r['n'],r['x'])
        if r['k']!=1 or r['n']!=26 or 'absolute' not in r['x'] or 'server baseline' not in r['note']: errs.append('SPECpower against a Mac baseline should stay absolute and say why')
        pg2=await b.new_page(viewport={'width':1360,'height':1100}); pg2.on('pageerror',lambda e:errs.append(str(e)))
        await pg2.goto(INDEX+'#cpu-all'); await pg2.wait_for_timeout(400); await pg2.select_option('#lbm',SPEC); await pg2.wait_for_timeout(200)
        await pg2.click('.tab[data-w="cpu-one"]'); await pg2.wait_for_timeout(250)
        r=await pg2.evaluate("({lbm:S.lbm,dis:document.querySelector('#lbm option[value=\"SPECpower_ssj2008\"]').disabled,b:JSON.stringify(S.base),n:S.pts.length})"); print('cpu-one after SPECpower',r)
        if r['lbm']!='Cinebench 2024' or not r['dis'] or r['b']!='{"chip":"M4 Max","dev":"MacBook Pro 14"}' or not r['n']: errs.append('leaving SPECpower did not restore Cinebench 2024 and the default baseline')
        # server rows stay out of the matrix and All workloads
        rows=await pg2.evaluate("[...document.querySelectorAll('#matrix tbody tr')].map(t=>t.textContent)")
        if any(('EPYC' in t or 'Xeon' in t or 'Ampere' in t or 'Grace' in t) for t in rows): errs.append('server chips leaked into the matrix')
        await pg2.select_option('#base',''); await pg2.click('.tab[data-w="all"]'); await pg2.wait_for_timeout(250)
        if await pg2.evaluate("S.pts.some(p=>p.r.o&&p.r.o.srv)"): errs.append('server rows leaked into All workloads')
        if not await pg2.evaluate("[...document.querySelectorAll('#base option')].some(o=>o.value==='AMD EPYC 9654|Lenovo ThinkSystem SR655 V3')"): errs.append('server machine missing from the baseline menu')
        # Blender server rows: borrowed SPECpower power, pe, psrc
        await pg2.click('.tab[data-w="blender"]'); await pg2.wait_for_timeout(250)
        bl=await pg2.evaluate("S.pts.filter(p=>p.r.srv).map(p=>({c:p.r.chip,pe:p.r.pe,est:p.r.est,ps:!!SRC[p.r.psrc],sp:/SPECpower/.test(p.r.note)}))"); print('blender server rows',len(bl))
        if len(bl)!=7 or not all(x['pe'] and x['est'] and x['ps'] and x['sp'] for x in bl): errs.append('Blender server rows missing or not marked as borrowed power')
        # phone width: no horizontal overflow on the server views
        pg3=await b.new_page(viewport={'width':390,'height':900}); pg3.on('pageerror',lambda e:errs.append(str(e)))
        await pg3.goto(INDEX+'#hpl'); await pg3.wait_for_timeout(400)
        sw=[await pg3.evaluate("document.documentElement.scrollWidth")]
        await pg3.click('.tab[data-w="cpu-all"]'); await pg3.select_option('#lbm',SPEC); await pg3.wait_for_timeout(300)
        sw.append(await pg3.evaluate("document.documentElement.scrollWidth"))
        await pg3.evaluate("document.getElementById('opts').open=true"); await pg3.wait_for_timeout(150); sw.append(await pg3.evaluate("document.documentElement.scrollWidth"))
        print('scrollWidth at 390',sw)
        if any(w>390 for w in sw): errs.append('horizontal overflow at 390px: '+str(sw))
        print('errors',errs); await b.close()
asyncio.run(main())
