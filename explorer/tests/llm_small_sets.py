"""oMLX small-model sets: each Model-menu entry isolates its set, every point is speed measured / power estimated with the chip's
Llama 2 7B power, baselines compare the same model, and the Qwen sets stay out of the default every-model view."""
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
        await pg.goto(INDEX); await pg.wait_for_timeout(400); await pg.evaluate("document.querySelector('.tab[data-w=\"llm\"]').click()"); await pg.wait_for_timeout(200)
        if await pg.evaluate("S.w")!='llm': errs.append('default tab is not LLM')
        if await pg.evaluate("S.pts.some(p=>p.r.set==='omlxq')"): errs.append('Qwen oMLX sets leaked into the every-model view')
        await pg.select_option('#base','M4|Mac mini')
        for v,n in (('Llama 3.2 3B 4-bit (oMLX)',18),('Llama 3.2 1B 4-bit (oMLX)',17),('set:omlxq',208)):
            await pg.select_option('#lmod',v); await pg.wait_for_timeout(250)
            r=await pg.evaluate("""()=>{const ll={};for(const r of ALL)if(r.w==='llm'&&r.model==='Llama 2 7B Q4_0'&&r.src==='llamacpp')ll[r.chip]=r.p;
              return {n:S.pts.length,sets:[...new Set(S.pts.map(p=>p.r.set))],pe:S.pts.every(p=>p.r.pe&&p.r.plo&&/oMLX/.test(p.r.note)&&p.r.p===ll[p.r.chip]),
              bad:S.pts.filter(p=>{const v=relOf(p.r);return v&&v.b.model!==p.r.model}).length,rel:S.pts.filter(p=>relOf(p.r)).length}}""")
            print(v,r)
            if r['n']!=n: errs.append(f'{v}: {r["n"]} points, expected {n}')
            if len(r['sets'])!=1 or not r['sets'][0].startswith('omlx'): errs.append(v+': set filter leaked')
            if not r['pe']: errs.append(v+': a point is not speed measured with the 7B power estimate')
            if r['bad']: errs.append(v+': baseline from another model')
            if v!='set:omlxq' and not r['rel']: errs.append(v+': no like-for-like M4 baseline')
        print('errors',errs); await b.close()
asyncio.run(main())
