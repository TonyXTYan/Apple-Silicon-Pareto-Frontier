import asyncio, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
OUT=str(HERE/'shots')+os.sep
os.makedirs(OUT,exist_ok=True)
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':1360,'height':1150}); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(''+INDEX+''); await pg.wait_for_timeout(500)
        await pg.evaluate("document.querySelectorAll('details').forEach(d=>d.open=true)")
        print('large by default', await pg.evaluate('S.looBig'))  # no Enlarge button any more
        await pg.locator('#loo').scroll_into_view_if_needed()
        pos=await pg.evaluate("""()=>{const L=S.loo,p=L.pts.find(p=>p.chip==='M4'&&p.w==='cpu-all')||L.pts[0];const b=L.svg.getBoundingClientRect(),k=b.width/L.svg.viewBox.baseVal.width;return [b.left+p.px*k,b.top+p.py*k]}""")
        await pg.mouse.move(pos[0],pos[1]); await pg.wait_for_timeout(250)
        await pg.locator('#loo').screenshot(path=OUT+'l1.png')
        print(await pg.evaluate("document.getElementById('lootip').innerText"))
        print('errors',errs); await b.close()
asyncio.run(main())
