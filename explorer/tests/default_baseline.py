"""Estimated M4 Max MacBook Pro 14 and the default baseline: the page opens on LLM with no baseline; the first switch to
another tab sets the M4 Max MacBook Pro 14 as baseline unless the user has chosen one (menu, matrix row, readout, Clear);
the 14-inch rows are estimates (speed borrowed, power capped at the adapter envelope) that serve as their own baseline on the
CPU and Gaming tabs, the chip's best row elsewhere, and show the ENERGY STAR figures."""
import asyncio, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
B="JSON.stringify(S.base)"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
        errs=[]
        async def page(h='',w=1360):
            pg=await b.new_page(viewport={'width':w,'height':1100}); pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.goto(INDEX+h); await pg.wait_for_timeout(400); return pg
        pg=await page()
        st=await pg.evaluate("S.w+' '+"+B); print('opens on',st)
        if st!='llm null': errs.append('page should open on LLM with no baseline')
        rows=await pg.evaluate("EST.filter(r=>r.chip==='M4 Max'&&r.dev==='MacBook Pro 14').map(r=>({w:r.w,g:r.game||'',p:r.p,lo:r.plo,hi:r.phi,q:r.q,pe:r.pe,brw:r.brw,es:!!(appleFor(r)||{}).es}))")
        print('14-inch rows',rows)
        if sorted((r['w'],r['g']) for r in rows)!=sorted([('cpu-all',''),('cpu-one',''),('gpu','Cyberpunk 2077'),('gpu',"Baldur's Gate 3"),('gpu',"Assassin's Creed Shadows")]): errs.append('14-inch rows missing')
        for r in rows:
            if not (r['pe'] and r['q']!='A' and r['brw']=='MacBook Pro 16' and r['p']<=97 and r['lo']<r['p']<=r['hi'] and r['es']): errs.append('14-inch row flags or power '+str(r))
        if not await pg.evaluate("[...document.querySelectorAll('#base option')].some(o=>o.value==='M4 Max|MacBook Pro 14')"): errs.append('M4 Max MacBook Pro 14 not in the baseline menu')
        await pg.click('.tab[data-w="cpu-all"]'); await pg.wait_for_timeout(300)
        r=await pg.evaluate("({b:"+B+",tb:tabBase(curBase()).map(r=>r.dev),ring:document.querySelectorAll('#chart .baseline-ring').length,k:G.k,lab:document.getElementById('basel').textContent,sel:document.getElementById('base').value})"); print('cpu-all after first switch',r)
        if r['b']!='{"chip":"M4 Max","dev":"MacBook Pro 14"}' or r['tb']!=['MacBook Pro 14'] or r['ring']!=1 or r['k']==1 or r['lab']!='Relative to' or r['sel']!='M4 Max|MacBook Pro 14': errs.append('default baseline not applied on cpu-all')
        # hover the baseline point: ENERGY STAR in the tooltip
        await pg.evaluate("(()=>{const q=S.pts.find(p=>p.r.dev==='MacBook Pro 14'&&p.r.chip==='M4 Max');showTip(q,'hover')})()")
        tip=await pg.evaluate("document.getElementById('tip').textContent"); print('tooltip',tip[:200])
        if 'ENERGY STAR' not in tip or 'speed borrowed' not in tip: errs.append('tooltip lacks ENERGY STAR figures or the borrowed-speed label')
        for tab,want in (('gpu','MacBook Pro 14'),('blender','MacBook Pro 16'),('hpl','Mac Studio'),('llm','MacBook Pro 16')):
            await pg.click(f'.tab[data-w="{tab}"]'); await pg.wait_for_timeout(250)
            r=await pg.evaluate("({b:"+B+",tb:tabBase(curBase()).map(r=>r.chip+' '+r.dev.replace(' (estimate)','')),games:S.w==='gpu'?['Cyberpunk 2077',\"Baldur's Gate 3\",\"Assassin's Creed Shadows\"].map(g=>baseRow('gpu',curBase(),g).dev):[],rel:S.pts.filter(p=>relOf(p.r)).length})"); print(tab,r)
            if r['b']!='{"chip":"M4 Max","dev":"MacBook Pro 14"}': errs.append(tab+': baseline changed')
            if not r['tb'] or any(not t.endswith(want) or not t.startswith('M4 Max') for t in r['tb']): errs.append(tab+': baseline row '+str(r['tb']))
            if tab=='gpu' and r['games']!=['MacBook Pro 14']*3: errs.append('gaming: the 14-inch should be the baseline in every game')
            if not r['rel']: errs.append(tab+': no ratios')
        # a user's own choice (None on LLM) wins over the default
        pg2=await page(); await pg2.select_option('#base',''); await pg2.click('.tab[data-w="cpu-one"]'); await pg2.wait_for_timeout(250)
        if await pg2.evaluate(B)!='null': errs.append('default baseline overrode the user choosing None')
        pg3=await page(); await pg3.evaluate("document.querySelector('#matrix tbody tr[tabindex]').click()"); await pg3.wait_for_timeout(200)
        chosen=await pg3.evaluate(B); await pg3.click('.tab[data-w="gpu"]'); await pg3.wait_for_timeout(250)
        if await pg3.evaluate(B)!=chosen: errs.append('default baseline overrode a matrix choice')
        pg4=await page(); await pg4.click('.tab[data-w="cpu-all"]'); await pg4.click('#mclear'); await pg4.click('.tab[data-w="gpu"]'); await pg4.wait_for_timeout(250)
        if await pg4.evaluate(B)!='null': errs.append('Clear baseline should stick')
        pg5=await page('#gpu',390)
        r=await pg5.evaluate("({b:"+B+",sw:document.documentElement.scrollWidth})"); print('#gpu at 390',r)
        if r['b']!='{"chip":"M4 Max","dev":"MacBook Pro 14"}' or r['sw']>390: errs.append('#gpu link at 390px: '+str(r))
        print('errors',errs); await b.close()
asyncio.run(main())
