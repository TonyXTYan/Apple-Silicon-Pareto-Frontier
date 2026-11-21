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
        print('all',await pg.evaluate("S.pts.length"))
        await pg.click('.tab[data-w="llm"]'); await pg.mouse.move(5,5)
        for v,f in [('set:mlx','c1'),('set:cluster','c2'),('','c3'),('Llama 3 8B Q4_K_M','c4')]:
            await pg.select_option('#lmod',v); await pg.wait_for_timeout(250); print(v,await pg.evaluate("S.pts.length")); await pg.locator('#wrap').screenshot(path=f+'.png')
        print('errors',errs); await b.close()
asyncio.run(main())
