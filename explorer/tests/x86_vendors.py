"""Comparison machines: four vendor colour groups with light and dark tokens, chip-tier chips for each, like-for-like
baselines against an AMD machine, same-vendor hover relatives, and matrix rows after the Apple chips."""
import asyncio, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
V=['Intel','AMD','Qualcomm','NVIDIA']
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
        errs=[]; cols={}
        for scheme in ('light','dark'):
            pg=await b.new_page(viewport={'width':1360,'height':1100},color_scheme=scheme); pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.goto(INDEX); await pg.wait_for_timeout(400)
            cols[scheme]=await pg.evaluate("['--s-intel','--s-amd','--s-qcom','--s-nv','--s-base','--s-pro','--s-max','--s-ultra'].map(k=>getComputedStyle(document.documentElement).getPropertyValue(k).trim())")
            if scheme=='dark': break
            print('default view',await pg.evaluate("S.w+' base='+JSON.stringify(S.base)"))
            if await pg.evaluate("S.w!=='cpu-all'||S.base!==null"): errs.append('default view changed')
            chips=await pg.evaluate("[...document.querySelectorAll('#tiers .chip')].map(c=>c.textContent.trim())"); print('tier chips',chips)
            if not all(v in chips for v in V): errs.append('vendor tier chips missing')
            vis=await pg.evaluate("[...new Set(S.pts.map(p=>p.r.tier))]"); print('LLM tiers shown',vis)
            if not {'AMD','NVIDIA','Intel'}<=set(vis): errs.append('comparison LLM rows missing')
            await pg.click('.tab[data-w="cpu-all"]'); await pg.select_option('#base','AMD Ryzen AI Max+ 395|Asus ROG Flow Z13 (2025)'); await pg.wait_for_timeout(300)
            r=await pg.evaluate("""()=>{const z=S.pts.find(p=>p.r.dev==='Asus ROG Flow Z13 (2025)');S.hover=z.r;drawFocus();const rel=relatives(z.r);
              return {k:G.k,rel:rel.gen.map(p=>p.r.tier),ring:document.querySelectorAll('#chart .baseline-ring').length,lab:[...document.querySelectorAll('#labels text')].map(t=>t.textContent)[0]}}""")
            print('cpu-all vs Z13',r)
            if r['ring']!=1 or not r['rel'] or set(r['rel'])!={'AMD'}: errs.append('baseline ring or same-vendor relatives broken')
            await pg.click('.tab[data-w="llm"]'); await pg.wait_for_timeout(300)
            bad=await pg.evaluate("S.pts.filter(p=>{const v=relOf(p.r);return v&&(v.b.model||'Llama 2 7B Q4_0')!==(p.r.model||'Llama 2 7B Q4_0')}).length"); n=await pg.evaluate("S.pts.filter(p=>relOf(p.r)).length")
            print('llm vs Z13 chip: points with a same-model baseline',n,'wrong model',bad)
            if bad or not n: errs.append('LLM baseline not like-for-like')
            rows=await pg.evaluate("[...document.querySelectorAll('#matrix tbody tr')].map(t=>t.className==='msep'?'|':t._k)")  # full chip name (the cell shows it without the vendor)
            i=rows.index('|') if '|' in rows else -1; print('matrix comparison rows',len(rows)-i-1)
            if i<0 or any(not x.startswith(tuple(V)) for x in rows[i+1:]) or any(x.startswith(tuple(V)) for x in rows[:i]): errs.append('matrix order or divider wrong')
            await pg.close()
        print('tokens light',cols['light'][:4],'dark',cols['dark'][:4])
        for s in ('light','dark'):
            if len(set(cols[s]))!=8 or '' in cols[s]: errs.append(s+' colour tokens missing or repeated')
        if cols['light'][:4]==cols['dark'][:4]: errs.append('dark tokens not stepped')
        print('errors',errs); await b.close()
asyncio.run(main())
