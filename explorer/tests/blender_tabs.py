import asyncio, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
OUT=str(HERE/'shots')+os.sep
os.makedirs(OUT,exist_ok=True)
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
async def pick(pg,box,v):
    """choose v in a filter chip group as a user would: a single-choice row is clicked; a multi-select group is reset with Show all, then v alone is clicked ('' leaves every option on)"""
    if await pg.locator(f'#{box} [role=radio]').count(): await pg.click(f'#{box} [data-opt="{v}"]'); return
    if await pg.locator(f'#{box} .showall.on').count(): await pg.click(f'#{box} .showall')
    if v!='': await pg.click(f'#{box} [data-opt="{v}"]')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':1360,'height':1150}); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(''+INDEX+''); await pg.wait_for_timeout(600)
        await pg.locator('#wrap').screenshot(path=OUT+'b1.png')
        await pg.locator('#tabs').screenshot(path=OUT+'b0.png')
        await pg.click('.tab[data-w="blender"]'); await pg.wait_for_timeout(300)
        print('tabs',await pg.evaluate("[...document.querySelectorAll('.tab')].map(t=>t.dataset.w).join()"))
        if await pg.locator('.tab[data-w="bl-cpu"]').count() or await pg.locator('.tab[data-w="bl-gpu"]').count(): errs.append('separate Blender tabs still drawn')
        ws=await pg.evaluate("[...new Set(S.pts.map(p=>p.r.w))].sort().join()"); print('blender tab workloads',ws)
        if ws!='bl-cpu,bl-gpu': errs.append('Blender tab should show CPU and GPU together')
        await pick(pg,'ldevw','bl-gpu'); await pg.wait_for_timeout(300)
        pos=await pg.evaluate("""()=>{const p=S.pts.find(p=>p.r.chip==='M3 Max');const svg=document.getElementById('chart'),b=svg.getBoundingClientRect(),k=b.width/svg.viewBox.baseVal.width;return [b.left+p.px*k,b.top+p.py*k]}""")
        await pg.mouse.move(pos[0]-20,pos[1]-20); await pg.mouse.move(pos[0],pos[1],steps=3); await pg.wait_for_timeout(250)
        await pg.locator('#wrap').screenshot(path=OUT+'b2.png')
        await pick(pg,'ldevw','bl-cpu'); await pg.wait_for_timeout(300)
        if await pg.evaluate("S.pts.some(p=>p.r.w!=='bl-cpu')"): errs.append('device filter leaked')
        await pg.locator('#wrap').screenshot(path=OUT+'b3.png')
        hm=await pg.evaluate("[...document.querySelectorAll('#matrix thead th')].map(t=>t.textContent).filter(t=>t.startsWith('Blender'))"); print('matrix Blender columns',hm)
        if len(hm)!=2: errs.append('matrix should keep Blender CPU and GPU columns')
        await pg.evaluate("document.getElementById('matrix').scrollIntoView()"); 
        await pg.locator('#matrix').screenshot(path=OUT+'b4.png')
        pg2=await b.new_page(viewport={'width':400,'height':900}); pg2.on('pageerror',lambda e:errs.append('m '+str(e)))
        await pg2.goto(INDEX+'#bl-gpu'); await pg2.wait_for_timeout(500); await pg2.locator('#wrap').screenshot(path=OUT+'b5.png')
        old=await pg2.evaluate("S.w+' '+S.ldev"); print('old #bl-gpu link opens',old)
        if old!='blender bl-gpu': errs.append('old Blender GPU link not mapped')
        print('errors',errs); await b.close()
asyncio.run(main())
