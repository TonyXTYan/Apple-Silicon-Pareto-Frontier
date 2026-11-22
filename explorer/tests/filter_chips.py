"""Per-tab filter chips (template.html: fchips, fradio, the Models panel, togSet, syncFilters). Multi-select groups follow the Chip tier
and Machine rule (the first click on a full set shows only that option, later clicks add or remove, emptying shows all, a fading Show
all restores everything); single-choice rows are role=radio. LLM: maker solo and toggle (with a mixed state), one model toggled on and
off, Show all, the Model size chips combined (AND), Collections filtered by the chips, and a one-model baseline. Gaming: one, two and
every game, with and without a baseline. Blender: Device chips and the Scene radio (keyboard too). Linear algebra: Sets chips and their
axes. CPU: the Benchmark radio (SPECpower hidden and skipped on the one-thread tab). Every chip's count matches the points it shows,
hovering an option highlights its points, changes animate, nothing overflows at 390px with every panel open, and no page errors."""
import asyncio, os, pathlib
HERE=pathlib.Path(__file__).resolve().parent
INDEX=(HERE.parent/'index.html').as_uri()
OUT=str(HERE/'shots')+os.sep
os.makedirs(OUT,exist_ok=True)
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
from playwright.async_api import async_playwright
BG,CP,AC="Baldur's Gate 3",'Cyberpunk 2077',"Assassin's Creed Shadows"
async def open_maker(pg,mk):
    """open a maker's list of models (the arrow beside the maker chip) unless it is open"""
    x=pg.locator(f'.mkp:has([data-maker="{mk}"]) .mkx')
    if await x.get_attribute('aria-expanded')!='true': await x.click()
async def show_all(pg,sel):
    if await pg.locator(sel+' .showall.on').count(): await pg.click(sel+' .showall')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':1360,'height':1100}); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        E=pg.evaluate
        def need(c,msg):
            if not c: errs.append(msg)
        await pg.goto(INDEX+'#llm'); await pg.wait_for_timeout(600); await pg.mouse.move(5,5)
        # ---------- LLM: makers ----------
        mk=await E("MK.map(x=>x[0])"); print('makers',mk)
        need(mk==['Qwen','Llama','Gemma','gpt-oss','DeepSeek','Mistral','Kimi','Other'],f'makers {mk}')
        need(await E("makerOf('Devstral Small 2 24B')==='Mistral'&&makerOf('Kimi K2 Thinking 1T')==='Kimi'&&makerOf('Phi-4 14B')==='Phi'&&makerOf('9B model, Q4')==='Other'"),'maker read from the name')
        need(await E("MK.reduce((a,x)=>a+x[1].length,0)===MODELS.length"),'every model under one maker')
        need(await E("document.querySelectorAll('.mkg:not([hidden])').length")==0,'model lists should start closed')
        n0=await E("S.pts.length"); print('every model',n0)
        await pg.click('[data-maker="Qwen"]'); await pg.wait_for_timeout(100)
        need(await E("document.getElementById('chart').classList.contains('pvanim')"),'a filter change should animate')
        await pg.wait_for_timeout(900)
        r=await E("({all:S.pts.every(p=>makerOf(mkey(p.r))==='Qwen'),n:S.pts.length,q:document.querySelector('[data-maker=Qwen]').getAttribute('aria-pressed'),l:document.querySelector('[data-maker=Llama]').getAttribute('aria-pressed'),sa:document.querySelector('#lml .showall').classList.contains('on'),cnt:document.querySelector('[data-maker=Qwen] small').textContent})")
        print('Qwen solo',r); need(r['all'] and r['n'] and r['q']=='true' and r['l']=='false' and r['sa'],'maker solo')
        need(r['cnt']==f"{r['n']:,}",f"Qwen chip count {r['cnt']} vs {r['n']} points")
        await pg.click('[data-maker="Llama"]'); await pg.wait_for_timeout(250)
        r=await E("[...new Set(S.pts.map(p=>makerOf(mkey(p.r))))].sort()"); print('Qwen + Llama',r); need(r==['Llama','Qwen'],'maker toggle on')
        await pg.click('[data-maker="Qwen"]'); await pg.wait_for_timeout(250)
        r=await E("[...new Set(S.pts.map(p=>makerOf(mkey(p.r))))]"); print('Qwen off',r); need(r==['Llama'],'maker toggle off')
        # one model off and on: the maker shows a mixed state
        await open_maker(pg,'Llama'); L2='Llama 2 7B Q4_0'
        await pg.click(f'[data-model="{L2}"]'); await pg.wait_for_timeout(250)
        r=await E(f"({{n:S.pts.filter(p=>p.r.model==='{L2}').length,m:document.querySelector('[data-maker=Llama]').getAttribute('aria-pressed'),c:document.querySelector('[data-model=\"{L2}\"]').getAttribute('aria-pressed'),lab:document.querySelector('[data-maker=Llama]').getAttribute('aria-label')}})")
        print('Llama 2 7B off',r); need(r['n']==0 and r['m']=='mixed' and r['c']=='false' and 'of' in r['lab'],'model toggle off / mixed maker')
        await pg.click(f'[data-model="{L2}"]'); await pg.wait_for_timeout(250)
        need(await E(f"S.pts.some(p=>p.r.model==='{L2}')&&document.querySelector('[data-maker=Llama]').getAttribute('aria-pressed')==='true'"),'model toggle back on')
        # emptying the set shows every model again
        await pg.click('[data-maker="Llama"]'); await pg.wait_for_timeout(250)
        r=await E("({n:S.pts.length,k:S.lmods.size===MODELS.length,sa:document.querySelector('#lml .showall').classList.contains('on')})"); print('emptied',r)
        need(r['n']==n0 and r['k'] and not r['sa'],'emptying the models should show all')
        # a model alone from the full set, and its chip count
        await open_maker(pg,'Qwen'); await pg.click('[data-model="Qwen3 14B"]'); await pg.wait_for_timeout(250)
        r=await E("({ms:[...new Set(S.pts.map(p=>mkey(p.r)))],n:S.pts.length,c:document.querySelector('[data-model=\"Qwen3 14B\"] small').textContent,o:oneModel(),lab:S.pts.map(p=>shortName(p.r)).filter(t=>/Qwen3 14B/.test(t)).length})")
        print('Qwen3 14B alone',r); need(r['ms']==['Qwen3 14B'] and r['o']=='Qwen3 14B' and r['c']==str(r['n']),'model solo / count')
        need(r['lab']==0,'labels should drop the model name when one model is shown')
        # Show all (the panel's)
        await pg.click('#lml .showall'); await pg.wait_for_timeout(250)
        need(await E("S.pts.length")==n0,'Show all should restore every model')
        # combined with Model size (AND)
        await pg.click('#lsizew [data-size="L"]'); await pg.click('[data-maker="Gemma"]'); await pg.wait_for_timeout(250)
        r=await E("({ok:S.pts.every(p=>makerOf(mkey(p.r))==='Gemma'&&psize(p.r)==='L'),n:S.pts.length,xs:document.querySelector('#lsizew [data-size=XS]').disabled,g:document.querySelector('[data-model=\"Gemma 3 1B\"]').classList.contains('zero'),q:document.querySelector('[data-model=\"Qwen3 0.6B 4-bit\"]').disabled})")
        print('Gemma and L',r); need(r['ok'] and r['n']>0,'size and maker should combine'); need(r['g'] and r['q'],'a model with no point under the size filter should be dimmed (and disabled when it is off)')
        await pg.click('#lsizew [data-size="all"]'); await pg.click('#lml .showall'); await pg.wait_for_timeout(250)
        # Collections filtered by the chips
        await pg.select_option('#lmod','set:mlx'); await pg.wait_for_timeout(250); nm=await E("S.pts.length")
        await pg.click('[data-maker="Qwen"]'); await pg.wait_for_timeout(250)
        r=await E("({set:[...new Set(S.pts.map(p=>p.r.set))],mk:[...new Set(S.pts.map(p=>makerOf(mkey(p.r))))],n:S.pts.length,gd:document.querySelector('[data-maker=Gemma]').disabled})")
        print('MLX vs GGUF, Qwen',nm,r); need(r['set']==['mlx'] and r['mk']==['Qwen'] and 0<r['n']<nm and r['gd'],'chips should filter within a collection')
        await pg.click('#lml .showall'); await pg.select_option('#lmod',''); await pg.wait_for_timeout(250)
        # one model and a baseline: the baseline compares that model, from any source
        await pg.select_option('#base','M3 Ultra|'); await open_maker(pg,'gpt-oss'); await pg.click('[data-model="gpt-oss 20B"]'); await pg.wait_for_timeout(300)
        r=await E("({t:tsub(),tb:tabBase(curBase()).map(r=>mkey(r)+' '+r.chip),ring:document.querySelectorAll('#chart .baseline-ring').length,bad:S.pts.filter(p=>{const v=relOf(p.r);return v&&mkey(v.b)!==mkey(p.r)}).length,x:document.getElementById('basex').textContent})")
        print('gpt-oss 20B vs M3 Ultra',r); need(r['t']=='model:gpt-oss 20B' and r['tb'] and all(t.startswith('gpt-oss 20B ') for t in r['tb']) and r['ring']==1 and not r['bad'],'one-model baseline')
        await pg.click('#lml .showall'); await pg.wait_for_timeout(250)
        need(await E("tsub()")==None,'no single model: no model baseline')
        await pg.select_option('#base',''); await pg.wait_for_timeout(200)
        # hover a maker: its points stay, the rest dim
        await pg.hover('[data-maker="Gemma"]'); await pg.wait_for_timeout(150)
        r=await E("({dim:S.pts.filter(p=>p.g.classList.contains('dim')).length,other:S.pts.filter(p=>makerOf(mkey(p.r))!=='Gemma').length,gdim:S.pts.filter(p=>makerOf(mkey(p.r))==='Gemma'&&p.g.classList.contains('dim')).length})")
        print('hover Gemma',r); need(r['dim']==r['other'] and r['dim']>0 and r['gdim']==0,'maker hover highlight')
        await open_maker(pg,'Llama'); await pg.hover(f'[data-model="{L2}"]'); await pg.wait_for_timeout(150)
        r=await E(f"S.pts.filter(p=>!p.g.classList.contains('dim')).every(p=>p.r.model==='{L2}')&&S.pts.some(p=>p.g.classList.contains('dim'))"); need(r,'model hover highlight')
        await pg.mouse.move(5,5); await pg.wait_for_timeout(100)
        need(await E("S.pts.every(p=>!p.g.classList.contains('dim'))"),'leaving a chip clears the highlight')
        # keyboard: Enter on a focused model chip toggles it
        await pg.focus('[data-model="Llama 3.3 70B"]'); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(250)
        need(await E("oneModel()")=='Llama 3.3 70B','Enter on a model chip')
        await pg.click('#lml .showall'); await pg.wait_for_timeout(200)
        await pg.locator('#lmodsw').screenshot(path=OUT+'fc_llm.png')
        # ---------- Gaming ----------
        await pg.click('.tab[data-w="gpu"]'); await pg.wait_for_timeout(300); await pg.mouse.move(5,5)
        G3="({g:[...new Set(S.pts.map(p=>p.r.game))].sort(),kg:!!perGame(),ax:!!axisRel(),iso:document.querySelectorAll('#chart .iso').length,lg:S.lgame,bad:S.pts.filter(p=>{const v=relOf(p.r);return v&&v.b.game!==p.r.game}).length,y:[...document.querySelectorAll('#chart .axt')].map(t=>t.textContent).join(' | ')})"
        r=await E(G3); print('every game, no baseline',r); need(r['g']==sorted([BG,CP,AC]) and not r['kg'] and not r['ax'] and r['iso']>0,'every game without a baseline')
        await pg.select_option('#base','M4 Max|MacBook Pro 16'); await pg.wait_for_timeout(250)
        r=await E(G3); print('every game, baseline',r); need(r['kg'] and r['iso']==0 and not r['bad'] and 'same game' in r['y'],'every game with a baseline: per-game ratio, no power lines')
        await pg.click(f'#lgamew [data-opt="{BG}"]'); await pg.wait_for_timeout(250)
        r=await E(G3); print('one game, baseline',r); need(r['g']==[BG] and r['lg']==BG and not r['kg'] and r['ax'] and r['iso']>0,'one game with a baseline: ratio axes for that game')
        await pg.click(f'#lgamew [data-opt="{CP}"]'); await pg.wait_for_timeout(250)
        r=await E(G3); print('two games, baseline',r); need(r['g']==sorted([BG,CP]) and r['lg']=='' and r['kg'] and r['iso']==0 and not r['bad'],'two games with a baseline: per-game ratio over the two')
        await pg.select_option('#base',''); await pg.wait_for_timeout(250)
        r=await E(G3); print('two games, no baseline',r); need(r['g']==sorted([BG,CP]) and not r['kg'] and not r['ax'] and r['iso']>0,'two games without a baseline')
        await pg.click(f'#lgamew [data-opt="{CP}"]'); await pg.wait_for_timeout(250)
        r=await E(G3); print('one game, no baseline',r); need(r['g']==[BG] and not r['ax'],'one game without a baseline')
        await pg.click('#lgamew .showall'); await pg.wait_for_timeout(250)
        r=await E(G3+".g"); need(r==sorted([BG,CP,AC]),'Show all games')
        c=await E("[...document.querySelectorAll('#lgamew [data-opt]')].map(b=>[b.dataset.opt,+b.querySelector('small').textContent])")
        for g,n in c:
            await pg.click(f'#lgamew [data-opt="{g}"]'); await pg.wait_for_timeout(200); k=await E("S.pts.length"); need(k==n,f'{g}: chip says {n}, plot has {k}')
            await pg.click('#lgamew .showall'); await pg.wait_for_timeout(200)
        await pg.hover(f'#lgamew [data-opt="{AC}"]'); await pg.wait_for_timeout(150)
        need(await E(f"S.pts.every(p=>p.g.classList.contains('dim')===(p.r.game!==\"{AC}\"))"),'game hover highlight')
        await pg.mouse.move(5,5); await pg.locator('#lgamew').screenshot(path=OUT+'fc_gpu.png')
        # ---------- Blender ----------
        await pg.click('.tab[data-w="blender"]'); await pg.wait_for_timeout(300)
        D="({w:[...new Set(S.pts.map(p=>p.r.w))].sort(),d:S.ldev,s:[...new Set(S.pts.map(p=>p.r.scene||''))],c:document.querySelector('#ldevw [data-opt=\"bl-cpu\"]').getAttribute('aria-pressed'),g:document.querySelector('#ldevw [data-opt=\"bl-gpu\"]').getAttribute('aria-pressed')})"
        r=await E(D); need(r['w']==['bl-cpu','bl-gpu'] and r['d']=='','both devices by default')
        await pg.click('#ldevw [data-opt="bl-cpu"]'); await pg.wait_for_timeout(250)
        r=await E(D); print('CPU',r); need(r['w']==['bl-cpu'] and r['d']=='bl-cpu' and r['c']=='true' and r['g']=='false','device solo')
        await pg.click('#ldevw [data-opt="bl-gpu"]'); await pg.wait_for_timeout(250)
        r=await E(D); need(r['w']==['bl-cpu','bl-gpu'] and r['d']=='','device toggle back')
        await pg.click('#ldevw [data-opt="bl-gpu"]'); await pg.wait_for_timeout(250)
        r=await E(D); need(r['w']==['bl-gpu'] and r['d']=='bl-gpu','device solo from both again')
        await pg.click('#ldevw [data-opt="bl-gpu"]'); await pg.wait_for_timeout(250)
        r=await E(D); need(r['w']==['bl-cpu','bl-gpu'],'emptying the devices shows both')
        need(await E("document.getElementById('lscenew').getAttribute('role')==='radiogroup'&&[...document.querySelectorAll('#lscenew [data-opt]')].every(b=>b.getAttribute('role')==='radio')"),'scene row is a radio group')
        need('alternative views' in (await E("document.getElementById('lscenew').title")),'scene tooltip should say why it is single-choice')
        await pg.click('#lscenew [data-opt="monster"]'); await pg.wait_for_timeout(250)
        r=await E(D+".s"); need(r==['monster'] and await E("S.lscene")=='monster','scene radio')
        need(await E("[...document.querySelectorAll('#lscenew [data-opt]')].map(b=>b.getAttribute('aria-checked')).join()")=='false,true,false,false','scene aria-checked')
        await pg.focus('#lscenew [data-opt="monster"]'); await pg.keyboard.press('ArrowRight'); await pg.wait_for_timeout(250)
        need(await E("S.lscene")=='junkshop' and await E("document.activeElement.dataset.opt")=='junkshop','scene radio: arrow key')
        await pg.keyboard.press('Home'); await pg.wait_for_timeout(250)
        need(await E("S.lscene")=='','scene radio: Home')
        await pg.locator('.vs').screenshot(path=OUT+'fc_blender.png')
        # ---------- Linear algebra ----------
        await pg.click('.tab[data-w="hpl"]'); await pg.wait_for_timeout(300); await pg.select_option('#base','M4|'); await pg.wait_for_timeout(250)
        H="({s:[...new Set(S.pts.map(p=>p.r.w==='hpl'?'hpl':p.r.set))].sort(),ls:S.lset,ax:!!axisRel(),bad:S.pts.filter(p=>{const v=relOf(p.r);return v&&(v.b.w!==p.r.w||v.b.set!==p.r.set||v.b.lib!==p.r.lib)}).length,ring:document.querySelectorAll('#chart .baseline-ring').length})"
        r=await E(H); print('HPL',r); need(r['s']==['hpl'] and r['ls']=='hpl' and r['ax'] and r['ring'],'HPL alone keeps ratio axes')
        await pg.click('#lsetw [data-opt="julia-sgemm"]'); await pg.wait_for_timeout(250)
        r=await E(H); print('HPL + fp32 GEMM',r); need(r['s']==['hpl','julia-sgemm'] and r['ls']=='' and not r['ax'] and not r['bad'] and r['ring']>=2,'mixed sets: absolute axes, ratios per set and library')
        await pg.click('#lsetw [data-opt="hpl"]'); await pg.wait_for_timeout(250)
        r=await E(H); print('fp32 GEMM',r); need(r['s']==['julia-sgemm'] and r['ls']=='julia-sgemm' and not r['ax'],'one GEMM set keeps absolute axes')
        await pg.click('#lsetw .showall'); await pg.wait_for_timeout(250)
        r=await E(H); need(r['s']==['arxiv-sgemm','hpl','julia-dgemm','julia-sgemm'] and not r['ax'],'Show all sets')
        await pg.select_option('#base',''); await pg.locator('.vs').screenshot(path=OUT+'fc_hpl.png')
        # ---------- CPU ----------
        await pg.click('.tab[data-w="cpu-all"]'); await pg.wait_for_timeout(300)
        need('own units' in (await E("document.getElementById('lbmw').title")),'benchmark tooltip should say why it is single-choice')
        await pg.click('#lbmw [data-opt="Geekbench 6"]'); await pg.wait_for_timeout(250)
        r=await E("({b:[...new Set(S.pts.map(p=>p.r.bm||'Cinebench 2024'))],c:document.querySelector('#lbmw [aria-checked=true]').dataset.opt,n:S.pts.length,k:+document.querySelector('#lbmw [aria-checked=true] small').textContent})")
        print('Geekbench 6',r); need(r['b']==['Geekbench 6'] and r['c']=='Geekbench 6' and r['n']==r['k'],'benchmark radio')
        need(not await E("document.querySelector('#lbmw [data-opt=\"SPECpower_ssj2008\"]').hidden"),'SPECpower on the all-cores tab')
        await pg.click('.tab[data-w="cpu-one"]'); await pg.wait_for_timeout(300)
        need(await E("document.querySelector('#lbmw [data-opt=\"SPECpower_ssj2008\"]').hidden"),'SPECpower hidden on the one-thread tab')
        await pg.click('#lbmw [data-opt="Cinebench 2026"]'); await pg.focus('#lbmw [data-opt="Cinebench 2026"]'); await pg.keyboard.press('ArrowRight'); await pg.wait_for_timeout(250)
        need(await E("S.lbm")=='Cinebench 2024','arrow keys should skip the hidden SPECpower')
        await pg.locator('.vs').screenshot(path=OUT+'fc_cpu.png')
        # ---------- 390px, every panel open, both themes ----------
        for scheme in ('light','dark'):
            pm=await b.new_page(viewport={'width':390,'height':900},color_scheme=scheme); pm.on('pageerror',lambda e:errs.append('m '+str(e)))
            for t in ('llm','gpu','blender','hpl','cpu-all','cpu-one','all'):
                await pm.goto(INDEX+'#'+t); await pm.wait_for_timeout(400)
                await pm.evaluate("()=>{document.querySelectorAll('.mkx[aria-expanded=false]').forEach(x=>x.click());document.getElementById('opts').open=true;document.getElementById('pdisp').open=true;document.getElementById('numbers').open=true;if(S.w==='llm'){document.querySelector('[data-maker=Qwen]').click()}}")
                await pm.wait_for_timeout(300)
                sw=await pm.evaluate("[document.documentElement.scrollWidth,document.body.scrollWidth,Math.max(...[...document.querySelectorAll('.vs *')].map(e=>e.getBoundingClientRect().right))]")
                if max(sw[:2])>390 or sw[2]>390: errs.append(f'{scheme} {t}: horizontal overflow at 390px {sw}')
                if t=='llm': await pm.locator('.vs').screenshot(path=OUT+f'fc_llm_390_{scheme}.png')
            await pm.close()
        print('errors',errs); await b.close()
asyncio.run(main())
