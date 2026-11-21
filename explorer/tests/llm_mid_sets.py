"""Mid-size oMLX sets: each Model-menu entry isolates its set, oMLX points are speed measured / power estimated with the chip's
Llama 2 7B power, the gpt-oss entry also shows the llama.cpp #15396 set and the metered gpt-oss runs, oMLX gpt-oss shares one
frontier with them, the other mid-size sets stay out of the default every-model view, and the new metered M3 Ultra / M4 Pro rows are there."""
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
        if await pg.evaluate("S.w")!='llm': errs.append('default tab is not LLM')
        if await pg.evaluate("S.pts.some(p=>p.r.set==='omlxl')"): errs.append('other mid-size oMLX sets leaked into the every-model view')
        if not await pg.evaluate("S.pts.some(p=>p.r.set==='omlx'&&p.r.model==='gpt-oss 20B (oMLX)')"): errs.append('oMLX gpt-oss 20B missing from the every-model view')
        m=await pg.evaluate("""ALL.filter(r=>r.w==='llm'&&!r.est&&(r.src==='geer_ai42'||r.src==='archy')).map(r=>[r.chip,r.model,r.p,r.q])""")
        print('metered',m)
        if sorted(m)!=sorted([['M3 Ultra','Qwen3 32B',227,'B'],['M3 Ultra','Llama 2 13B',227,'B'],['M4 Pro','Qwen3 32B',40,'C']]): errs.append('metered mid-size rows differ')
        await pg.select_option('#base','M4|Mac mini')
        for v,n in (('gpt-oss 20B (oMLX)',19),('Qwen3 14B (oMLX)',19),('Qwen3.5 27B (oMLX)',17),('set:omlxl',274)):
            await pg.select_option('#lmod',v); await pg.wait_for_timeout(250)
            r=await pg.evaluate("""()=>{const ll={};for(const r of ALL)if(r.w==='llm'&&r.model==='Llama 2 7B Q4_0'&&r.src==='llamacpp')ll[r.chip]=r.p;
              const om=S.pts.filter(p=>/^omlx/.test(p.r.set||''));
              return {n:om.length,sets:[...new Set(om.map(p=>p.r.set))],pe:om.every(p=>p.r.pe&&p.r.plo&&/oMLX/.test(p.r.note)&&p.r.p===ll[p.r.chip]),
              lcpp:S.pts.filter(p=>p.r.set==='lcpp').length,meas:S.pts.filter(p=>!p.r.est).length,
              bad:S.pts.filter(p=>{const v=relOf(p.r);return v&&v.b.model!==p.r.model}).length,rel:S.pts.filter(p=>relOf(p.r)).length}}""")
            print(v,r)
            if r['n']!=n: errs.append(f'{v}: {r["n"]} oMLX points, expected {n}')
            if len(r['sets'])!=1 or r['sets'][0]!=('omlxl' if v=='set:omlxl' else 'omlx'): errs.append(v+': set filter leaked')
            if not r['pe']: errs.append(v+': a point is not speed measured with the 7B power estimate')
            if r['bad']: errs.append(v+': baseline from another model')
            if v.startswith('gpt-oss'):
                if r['lcpp']!=7: errs.append(f'gpt-oss: {r["lcpp"]} llama.cpp points, expected 7')
                if r['meas']<2: errs.append('gpt-oss: metered gpt-oss 20B runs missing')
            elif r['lcpp']: errs.append(v+': llama.cpp gpt-oss points leaked')
            if v!='set:omlxl' and not r['rel']: errs.append(v+': no like-for-like M4 baseline')
        # frontier grouping: oMLX, llama.cpp and Geerling's gpt-oss 20B share one key
        await pg.select_option('#base',''); await pg.select_option('#lmod','gpt-oss 20B (oMLX)'); await pg.wait_for_timeout(250)
        k=await pg.evaluate("[...new Set(S.pts.map(p=>(p.r.ow||p.r.w)+'|'+String(vk(p.r)||'').replace(' (oMLX)','')))]")
        print('frontier keys',k)
        if k!=['llm|gpt-oss 20B']: errs.append('gpt-oss 20B points do not share one frontier key')
        # L size chip keeps the mid-size models only
        await pg.select_option('#lmod',''); await pg.evaluate("S.lsize=new Set(['L']);all()"); await pg.wait_for_timeout(250)
        bad=await pg.evaluate("S.pts.filter(p=>{const b=pcount(p.r);return b==null||b<12||b>=50}).map(p=>p.r.model)")
        if bad: errs.append('L size chip lets through '+str(sorted(set(bad))))
        print('errors',errs); await b.close()
asyncio.run(main())
