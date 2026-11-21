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
        pg=await b.new_page(viewport={'width':1360,'height':1000}); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(''+INDEX+''); await pg.wait_for_timeout(500)
        await pg.click('.tab[data-w="cpu-all"]'); await pg.wait_for_timeout(200)
        bb=await pg.locator('#chart').bounding_box(); cx,cy=bb['x']+bb['width']*0.4,bb['y']+bb['height']*0.3
        await pg.mouse.move(cx,cy)
        for i in range(4): await pg.mouse.wheel(0,-200); await pg.wait_for_timeout(60)
        print('zoom',await pg.evaluate("JSON.stringify(S.zoom)"))
        await pg.mouse.move(cx,cy); await pg.mouse.down(); await pg.mouse.move(cx+120,cy+60,steps=6); await pg.mouse.up()
        print('after pan',await pg.evaluate("S.zoom&&[S.zoom.x0.toFixed(0),S.zoom.x1.toFixed(0)]"),'pin',await pg.evaluate("!!S.pin"))
        await pg.locator('#wrap').screenshot(path=OUT+'z1.png')
        await pg.click('#zfs'); await pg.wait_for_timeout(400)
        await pg.screenshot(path=OUT+'z2.png')
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
        await pg.mouse.dblclick(cx,cy); await pg.wait_for_timeout(200)
        print('reset',await pg.evaluate("S.zoom"), 'fs',await pg.evaluate("document.getElementById('wrap').classList.contains('fs')"))
        print('errors',errs); await b.close()
asyncio.run(main())
