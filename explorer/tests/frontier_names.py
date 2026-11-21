"""With the frontier drawn, every benchmark/model group of two or more points gets a frontier line and (on wide screens) a name,
names never overlap each other, and hovering a name highlights its own frontier."""
import asyncio, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
CHECK="""()=>{const g=new Map();for(const p of S.pts){if(!S.fest&&(p.r.est||p.r.pe))continue;const k=(p.r.ow||p.r.w)+'|'+String(vk(p.r)||'').replace(' (oMLX)','');g.set(k,(g.get(k)||0)+1)}
  const want=[...g].filter(x=>x[1]>=2).map(x=>x[0]),lines=new Set([...document.querySelectorAll('#chart path.front')].map(p=>p.dataset.fk)),
  labs=[...document.querySelectorAll('#chart .flab')],bx=labs.map(t=>t.getBBox());let ov=0;
  for(let i=0;i<bx.length;i++)for(let j=i+1;j<bx.length;j++){const a=bx[i],b=bx[j];if(a.x<b.x+b.width-1&&b.x<a.x+a.width-1&&a.y<b.y+b.height-2&&b.y<a.y+a.height-2)ov++}
  return {want:want.length,missingLines:want.filter(k=>!lines.has(k)),labels:labs.length,overlaps:ov,sw:document.documentElement.scrollWidth}}"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox']); errs=[]
        for vw in (1440,390):
            pg=await b.new_page(viewport={'width':vw,'height':1000}); pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.goto(INDEX); await pg.wait_for_timeout(500); await pg.evaluate("document.getElementById('front').click()"); await pg.wait_for_timeout(200)
            r=await pg.evaluate(CHECK); print(vw,r)
            if r['missingLines']: errs.append(f'{vw} missing lines {r["missingLines"][:3]}')
            if r['overlaps']: errs.append(f'{vw} {r["overlaps"]} overlapping names')
            if vw>700 and r['labels']<r['want']: errs.append(f'{vw} only {r["labels"]} names for {r["want"]} frontiers')
            if vw<700 and r['sw']>vw: errs.append(f'overflow {r["sw"]}')
            if vw>700:
                await pg.locator('#chart .flab').first.hover(); await pg.wait_for_timeout(250)
                h=await pg.evaluate("[document.querySelectorAll('#chart .fon').length,document.querySelector('#chart g.fhov')!==null]"); print('hover',h)
                if not h[0] or not h[1]: errs.append(f'hover highlight {h}')
        print('errors',errs); await b.close()
asyncio.run(main())
