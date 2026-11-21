"""Apple's published power figures: laptops show environmental-report idle (display on), sleep, off, adapter and battery; desktops
show the support-page idle and maximum; the labels never mix the two idle definitions; clusters and comparison machines get none;
only desktop maxima clip estimates; the readout links Apple's sources."""
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
        await pg.goto(INDEX+'#cpu-all'); await pg.wait_for_timeout(400)
        r=await pg.evaluate("""()=>{const t=(chip,dev)=>{const p=S.pts.find(p=>p.r.chip===chip&&p.r.dev===dev);pin(p.r);showTip(p,'hover');
            return {tip:document.getElementById('tip').innerText,ro:document.getElementById('readout').innerText,links:[...document.querySelectorAll('#readout .apcite a')].map(a=>a.href)}};
          return {lap:t('M3 Max','MacBook Pro 14'),mini:t('M2','Mac mini'),x86:t('AMD Ryzen AI Max+ 395','Asus ROG Flow Z13 (2025)'),
            m1:APPLE.find(a=>a.chip==='M1'&&a.dev==='Mac mini').idle,nlap:APPLE.filter(a=>a.kind==='laptop').length,
            cluster:ALL.filter(r=>r.nodes>1).some(r=>appleFor(r)),lapclip:ALL.some(r=>r.clip&&r.form!=='desktop')}}""")
        lap,mini=r['lap'],r['mini']; print('laptop:',[l for l in lap['tip'].split('\n') if 'Apple' in l]); print('mini:',[l for l in mini['tip'].split('\n') if 'Apple' in l])
        print('m1 idle',r['m1'],'laptop entries',r['nlap'])
        if not all(s in lap['tip'] for s in ('idle 4.07 W (display on, M3 Pro table)','96 W adapter','72.4 Wh battery','sleep 0.26 W')): errs.append('laptop Apple figures missing')
        if 'max' in lap['tip'].split('Apple:')[1].split('\n')[0]: errs.append('laptop shows a maximum')
        if 'idle 7 W, max 50 W for a CPU-only load (support page)' not in mini['tip'] or 'display on' in mini['tip']: errs.append('desktop Apple figures wrong or mixed with the laptop idle')
        if 'Apple' in r['x86']['tip']: errs.append('comparison machine shows Apple figures')
        if r['cluster']: errs.append('cluster shows Apple figures')
        if r['lapclip']: errs.append('a laptop estimate is clipped by an Apple figure')
        if r['m1']!=6.8: errs.append('M1 Mac mini idle is not 6.8 W')
        if r['nlap']<28: errs.append('laptop entries missing')
        if not any('apple.com/environment' in u for u in lap['links']) or not any('support.apple.com' in u for u in mini['links']): errs.append('readout lacks links to Apple sources')
        if 'not measurements' not in lap['ro']: errs.append('readout does not say these are specifications')
        if not await pg.evaluate("[...document.querySelectorAll('#method li')].some(l=>/Apple's published power figures/.test(l.textContent))"): errs.append('method item missing')
        print('errors',errs); await b.close()
asyncio.run(main())
