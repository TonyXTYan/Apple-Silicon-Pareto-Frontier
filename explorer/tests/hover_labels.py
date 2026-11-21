"""Hovering any point shows its own label, in the main chart (every tab) and in the leave-one-out plot."""
import asyncio, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
MAIN="""async(w)=>{const out={n:0,miss:[]};const svg=document.getElementById('chart');
  for(const p of S.pts){S.hover=p.r;drawFocus();const want=shortName(p.r);const t=[...svg.querySelectorAll('#labels text')].find(t=>t.textContent===want);out.n++;if(!t)out.miss.push(want)}
  S.hover=null;drawFocus();return out}"""
LOO="""async()=>{const L=S.loo,svg=L.svg,b=svg.getBoundingClientRect(),k=b.width/svg.viewBox.baseVal.width;const out={n:0,miss:0,overlap:0};
  for(const p of L.pts){looTip({clientX:b.left+p.px*k,clientY:b.top+p.py*k});out.n++;
    const vis=[...svg.querySelectorAll('text')].filter(t=>t.closest('#loohl')||(t.classList.contains('loolbl')&&t.style.display!=='none'&&t._p===p));
    const own=vis.find(t=>t.closest('#loohl')||t._p===p);if(!own){out.miss++;continue}
    const a=own.getBBox();for(const o of svg.querySelectorAll('.loolbl')){if(o===own||o.style.display==='none')continue;const q=o.getBBox();if(q.x<a.x+a.width&&q.x+q.width>a.x&&q.y<a.y+a.height&&q.y+q.height>a.y)out.overlap++}}
  return out}"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
        errs=[]
        for vw in (1360,390):
            pg=await b.new_page(viewport={'width':vw,'height':1000}); pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.goto(INDEX); await pg.wait_for_timeout(600)
            for w in await pg.evaluate("[...document.querySelectorAll('.tab')].map(t=>t.dataset.w)"):
                await pg.evaluate(f"document.querySelector('.tab[data-w=\"{w}\"]').click()"); await pg.wait_for_timeout(150)
                r=await pg.evaluate(MAIN,w); print(vw,w,'points',r['n'],'missing labels',len(r['miss']),r['miss'][:3])
                if r['miss']: errs.append(f'{vw} {w} missing {r["miss"][:3]}')
            for big in (False,True):
                if big and vw<700: continue
                await pg.evaluate(f"S.looBig={'true' if big else 'false'};looPlot()"); await pg.wait_for_timeout(200)  # the plot is large by default on wide screens
                r=await pg.evaluate(LOO); print(vw,'loo big' if big else 'loo','points',r['n'],'missing',r['miss'],'overlaps',r['overlap'])
                if r['miss'] or r['overlap']: errs.append(f'loo {vw} {big} {r}')
        print('errors',errs); await b.close()
asyncio.run(main())
