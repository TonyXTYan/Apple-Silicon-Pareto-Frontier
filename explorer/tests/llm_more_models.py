"""Small variants of the newer families (oMLX, llm6.py): Qwen3.5 0.8B/2B/4B/9B, Qwen3.8 9B, Gemma 3 1B/4B, Gemma 3n E4B, Gemma 4 E2B/E4B in the
small set and Gemma 4 12B in the mid-size set; each has at least eight chips, one speed-measured point per chip with the chip's Llama 2 7B power
estimate, none leaks into the every-model view, the size chips read the names, the bandwidth sanity bound holds, and Qwen3.5 9B shares a frontier
key with the MLX-vs-GGUF Qwen3.5 9B rows."""
import asyncio, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
# model -> (chips, size chip, lower bound on GB streamed per token, as in llm6.py)
MODELS={'Qwen3.5 0.8B (oMLX)':(16,'XS',0.4),'Qwen3.5 2B (oMLX)':(18,'S',1.0),'Qwen3.5 4B (oMLX)':(19,'S',2.2),'Qwen3.5 9B 4-bit (oMLX)':(20,'M',4.4),
 'Qwen3.8 9B (oMLX)':(13,'M',4.4),'Gemma 3 1B (oMLX)':(8,'XS',0.55),'Gemma 3 4B (oMLX)':(19,'S',2.2),'Gemma 3n E4B (oMLX)':(10,'S',2.0),
 'Gemma 4 E4B (oMLX)':(19,'S',2.0),'Gemma 4 E2B (oMLX)':(18,'S',1.0),'Gemma 4 12B (oMLX)':(20,'L',6.0)}
BW={'M1':68,'M1 Pro':200,'M1 Max':400,'M1 Ultra':800,'M2':100,'M2 Pro':200,'M2 Max':400,'M2 Ultra':800,'M3':100,'M3 Pro':150,'M3 Max':400,'M3 Ultra':819,
    'M4':120,'M4 Pro':273,'M4 Max':546,'M5':153,'M5 Pro':307,'M5 Max':614,'M5 Ultra':1228}   # the larger GPU bin's bandwidth: a looser bound than llm6.py's
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':1360,'height':1100}); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(INDEX); await pg.wait_for_timeout(400); await pg.evaluate("document.querySelector('.tab[data-w=\"llm\"]').click()"); await pg.wait_for_timeout(200)
        if await pg.evaluate("S.w")!='llm': errs.append('default tab is not LLM')
        names=list(MODELS)
        if not await pg.evaluate("names=>names.every(n=>S.pts.some(p=>p.r.model===n))",names): errs.append('every-model view should include every new oMLX model')
        r=await pg.evaluate("""names=>{const o=ALL.filter(r=>r.w==='llm'&&names.includes(r.model));
          const ll={};for(const r of ALL)if(r.w==='llm'&&r.model==='Llama 2 7B Q4_0'&&r.src==='llamacpp')ll[r.chip]=r.p;
          const by={};for(const r of o)(by[r.model]=by[r.model]||[]).push(r);
          return {by:Object.fromEntries(Object.entries(by).map(([m,v])=>[m,{n:v.length,chips:new Set(v.map(r=>r.chip)).size,sets:[...new Set(v.map(r=>r.set))],size:[...new Set(v.map(r=>psize(r)))],
            pe:v.every(r=>r.pe&&r.est&&r.plo&&/oMLX/.test(r.note)&&r.p===ll[r.chip]),src:[...new Set(v.map(r=>r.src))].length,
            rows:v.map(r=>[r.chip,r.x,r.q,r.bench])}]))}}""",names)
        for m,(n,sz,gb) in MODELS.items():
            v=r['by'].get(m)
            if not v: errs.append(m+': missing'); continue
            if v['n']!=n or v['chips']!=n: errs.append(f"{m}: {v['n']} points on {v['chips']} chips, expected {n}")
            if v['sets']!=['omlxl' if '12B' in m else 'omlxq']: errs.append(f"{m}: set {v['sets']}")
            if v['size']!=[sz]: errs.append(f"{m}: size chip {v['size']}, expected {sz}")
            if not v['pe']: errs.append(m+': a point is not speed measured with the 7B power estimate')
            if v['src']!=1: errs.append(m+': more than one source key')
            for chip,x,q,bench in v['rows']:
                if chip in BW and x*gb>BW[chip]: errs.append(f'{m} {chip}: {x} tok/s x {gb} GB exceeds {BW[chip]} GB/s')
                if q not in 'BE': errs.append(f'{m} {chip}: grade {q}')
                if 'median of 1 run' in bench and q!='B': errs.append(f'{m} {chip}: single run not graded B')
        print({m:(v['n'],v['size']) for m,v in r['by'].items()})
        # Collection menu: the small and mid-size entries show them, and nothing else changes in those sets' every-model exclusion
        for sv,want_models in (('set:omlxq',[m for m in names if '12B' not in m]),('set:omlxl',['Gemma 4 12B (oMLX)'])):
            await pg.select_option('#lmod',sv); await pg.wait_for_timeout(250)
            got=await pg.evaluate("names=>[...new Set(S.pts.filter(p=>names.includes(p.r.model)).map(p=>p.r.model))]",names)
            if sorted(got)!=sorted(want_models): errs.append(f'{sv}: shows {sorted(got)}')
        # size chips: S keeps the 2-5B models and none of the others
        await pg.select_option('#lmod','set:omlxq'); await pg.evaluate("S.lsize=new Set(['S']);all()"); await pg.wait_for_timeout(250)
        bad=await pg.evaluate("S.pts.filter(p=>{const b=pcount(p.r);return b==null||b<2||b>=5}).map(p=>p.r.model)")
        if bad: errs.append('S size chip lets through '+str(sorted(set(bad))))
        got=await pg.evaluate("[...new Set(S.pts.map(p=>p.r.model))]")
        for m in ('Qwen3.5 2B (oMLX)','Qwen3.5 4B (oMLX)','Gemma 3 4B (oMLX)','Gemma 3n E4B (oMLX)','Gemma 4 E4B (oMLX)','Gemma 4 E2B (oMLX)'):
            if m not in got: errs.append('S size chip lost '+m)
        # a single-model entry and the frontier key of Qwen3.5 9B (oMLX) with the MLX-vs-GGUF Qwen3.5 9B rows
        k=await pg.evaluate("""()=>{const a=ALL.find(r=>r.model==='Qwen3.5 9B 4-bit (oMLX)'),b=ALL.find(r=>r.model==='Qwen3.5 9B 4-bit'&&r.set==='mlx');
          return [String(vk(a)||'').replace(' (oMLX)',''),String(vk(b)||'').replace(' (oMLX)','')]}""")
        print('frontier keys',k)
        if not k[0] or k[0]!=k[1]: errs.append('Qwen3.5 9B oMLX and MLX-vs-GGUF rows do not share a frontier key')
        # phone width
        await pg.set_viewport_size({'width':390,'height':800}); await pg.select_option('#lmod','set:omlxq'); await pg.wait_for_timeout(250)
        sw=await pg.evaluate("document.documentElement.scrollWidth")
        if sw>390: errs.append(f'scrollWidth {sw} at 390')
        print('errors',errs); await b.close()
asyncio.run(main())
