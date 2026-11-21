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
        await pg.goto(INDEX+'#gpu'); await pg.wait_for_timeout(500); await pg.mouse.move(5,5)
        print('tab',await pg.evaluate("S.w"),'game chips visible',await pg.is_visible('#lgamew'))
        opts=await pg.evaluate("[...document.querySelectorAll('#lgamew [data-opt]')].map(o=>o.dataset.opt)")
        print('every game pts',await pg.evaluate("S.pts.length"),'frontier groups',await pg.evaluate("new Set(S.pts.filter(p=>p.front).map(p=>p.r.game)).size"))
        await pg.locator('#wrap').screenshot(path=OUT+'g0.png')
        for i,g in enumerate(o for o in opts if o):
            await pick(pg,'lgamew',g); await pg.wait_for_timeout(300)
            n=await pg.evaluate("S.pts.length"); games=await pg.evaluate("[...new Set(S.pts.map(p=>p.r.game))]")
            print(g,'pts',n,'games',games)
            if games!=[g]: errs.append('game filter leaked: '+g)
            await pg.locator('#wrap').screenshot(path=OUT+f'g{i+1}.png')
        # baseline compares the same game
        await pick(pg,'lgamew',"Baldur's Gate 3"); await pg.select_option('#base','M4 Max|MacBook Pro 16'); await pg.wait_for_timeout(300)
        bad=await pg.evaluate("S.pts.filter(p=>{const v=relOf(p.r);return !v||v.b.game!==p.r.game}).length")
        print('bg3 vs M4 Max: axis k',await pg.evaluate("G.k.toFixed(3)"),'rows with wrong-game baseline',bad)
        if bad: errs.append('baseline from another game')
        await pick(pg,'lgamew',''); await pg.wait_for_timeout(300)
        bad=await pg.evaluate("S.pts.filter(p=>{const v=relOf(p.r);return v&&v.b.game!==p.r.game}).length")
        print('every game, wrong-game baselines',bad)
        if bad: errs.append('baseline from another game (every game)')
        await pg.click('.tab[data-w="llm"]'); await pg.wait_for_timeout(200)
        print('game chips hidden on llm',await pg.is_hidden('#lgamew'))
        await pg.click('.tab[data-w="all"]'); await pg.wait_for_timeout(200)
        print('all view gpu games',await pg.evaluate("[...new Set(S.pts.filter(p=>p.r.ow==='gpu').map(p=>p.r.o.game))]"))
        print('errors',errs); await b.close()
asyncio.run(main())
