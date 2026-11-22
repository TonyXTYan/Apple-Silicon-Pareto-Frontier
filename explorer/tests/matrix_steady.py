"""Previewing matrix rows (hover) never moves the table: the key above it keeps its tallest height at this width."""
import asyncio, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
J="document.getElementById('matrix').parentElement.getBoundingClientRect().top+scrollY"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox']); errs=[]
        for vw in (1440,390):
            pg=await b.new_page(viewport={'width':vw,'height':1000}); pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.goto(INDEX); await pg.wait_for_timeout(700); await pg.locator('#matrix').scroll_into_view_if_needed()
            top0=await pg.evaluate(J); rows=pg.locator('#matrix tbody tr[tabindex]'); n=await rows.count(); shifts=[]
            for i in (0,n//3,2*n//3,n-1):
                await rows.nth(i).hover(); await pg.wait_for_timeout(120); shifts.append(round(await pg.evaluate(J)-top0,1))
            print(vw,'shifts',shifts)
            if any(abs(s)>0.5 for s in shifts): errs.append(f'{vw}: table moved {shifts}')
        print('errors',errs); await b.close()
asyncio.run(main())
