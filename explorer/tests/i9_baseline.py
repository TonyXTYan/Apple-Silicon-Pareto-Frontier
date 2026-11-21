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
        await pg.goto(''+INDEX+''); await pg.wait_for_timeout(600)
        print('base',await pg.evaluate("JSON.stringify(S.base)"),'sel',await pg.evaluate("document.getElementById('base').value"),'pts',await pg.evaluate("S.pts.length"))
        print(await pg.evaluate("document.getElementById('wnote').textContent.slice(-220)"))
        await pg.locator('#wrap').screenshot(path=OUT+'i1.png')
        pos=await pg.evaluate("""()=>{const p=S.pts.find(p=>p.r.chip==='M4'&&p.r.ow==='cpu-all'&&p.r.dev==='Mac mini');const svg=document.getElementById('chart'),b=svg.getBoundingClientRect(),k=b.width/svg.viewBox.baseVal.width;return [b.left+p.px*k,b.top+p.py*k]}""")
        await pg.mouse.move(pos[0]-20,pos[1]-20); await pg.mouse.move(pos[0],pos[1],steps=3); await pg.wait_for_timeout(250)
        print(await pg.evaluate("document.getElementById('tip').innerText.slice(0,300)"))
        await pg.mouse.move(5,5)
        await pg.click('.tab[data-w="cpu-all"]'); await pg.wait_for_timeout(300); await pg.locator('#wrap').screenshot(path=OUT+'i2.png')
        await pg.select_option('#base',''); await pg.click('.tab[data-w="all"]'); await pg.wait_for_timeout(300); await pg.locator('#wrap').screenshot(path=OUT+'i3.png')
        await pg.evaluate("document.getElementById('matrix').scrollIntoView()"); await pg.locator('#matrix').screenshot(path=OUT+'i4.png')
        print('errors',errs); await b.close()
asyncio.run(main())
