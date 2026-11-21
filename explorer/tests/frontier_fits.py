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
        await pg.click('.tab[data-w="cpu-all"]'); await pg.check('#front'); await pg.wait_for_timeout(300)
        await pg.locator('#wrap').screenshot(path=OUT+'g1.png')
        for v in ['exp','log','lin']:
            await pg.select_option('#ffit',v); await pg.wait_for_timeout(200)
        await pg.locator('#wrap').screenshot(path=OUT+'g2.png')
        await pg.select_option('#ffit','pow'); await pg.click('.tab[data-w="all"]'); await pg.wait_for_timeout(300); await pg.mouse.move(5,5)
        await pg.locator('#wrap').screenshot(path=OUT+'g3.png')
        print('errors',errs); await b.close()
asyncio.run(main())
