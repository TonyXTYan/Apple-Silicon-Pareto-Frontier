"""-> data10.json  Intel, AMD, Qualcomm and NVIDIA comparison machines (the 13-machine shortlist in x86_rows.json):
Cinebench 2024, Cyberpunk 2077 and HPL rows with Notebookcheck or Jeff Geerling wall power, Geerling LLM runs (peak wall
power), and Blender Open Data medians for their chips with power estimated as for the Apple chips."""
import json, math
D=json.load(open('data9.json')); X=json.load(open('x86_rows.json'))['rows']
# source chip (prefix match, first wins) -> page chip, vendor tier, short label
CHIPS=[('Ryzen AI Max+ 395','AMD Ryzen AI Max+ 395','AMD','395'),('Radeon 8060S','AMD Ryzen AI Max+ 395','AMD','395'),
       ('Ryzen AI 9 HX 370','AMD Ryzen AI 9 HX 370','AMD','HX 370'),('Radeon 890M','AMD Ryzen AI 9 HX 370','AMD','HX 370'),
       ('Ryzen 7 8845HS','AMD Ryzen 7 8845HS','AMD','8845HS'),('Radeon 780M','AMD Ryzen 7 8845HS','AMD','8845HS'),
       ('Core Ultra 7 155H','Intel Core Ultra 7 155H','Intel','155H'),('Core Ultra 7 258V','Intel Core Ultra 7 258V','Intel','258V'),('Arc 140V','Intel Core Ultra 7 258V','Intel','258V'),
       ('Core Ultra X7 358H','Intel Core Ultra X7 358H','Intel','358H'),('Arc B390','Intel Core Ultra X7 358H','Intel','358H'),
       ('Core Ultra 9 275HX','Intel Core Ultra 9 275HX','Intel','275HX'),('Core Ultra 7 265K','Intel Core Ultra 7 265K','Intel','265K'),('Core 5 320','Intel Core 5 320','Intel','Core 5 320'),
       ('Snapdragon X Elite X1E-84-100','Qualcomm Snapdragon X Elite X1E-84-100','Qualcomm','X Elite'),
       ('GB10','NVIDIA GB10','NVIDIA','GB10'),('GeForce RTX 4090 (desktop)','NVIDIA GeForce RTX 4090','NVIDIA','RTX 4090'),('GeForce RTX 5090 Laptop','NVIDIA GeForce RTX 5090 Laptop','NVIDIA','RTX 5090 Laptop')]
# source device (prefix match) -> page device, form, short label
DEVS=[('Asus ROG Flow Z13','Asus ROG Flow Z13 (2025)','laptop','Z13'),('Framework Desktop mainboard','Framework Desktop mainboard','desktop','Framework board'),
      ('Framework Desktop','Framework Desktop','desktop','Framework'),('Asus Zenbook S 16','Asus Zenbook S 16 UM5606','laptop','Zenbook S16'),
      ('Asus ProArt P16','Asus ProArt P16 (RTX 5090 Laptop)','laptop','ProArt P16'),('Schenker VIA 14 Pro','Schenker VIA 14 Pro (M24)','laptop','VIA 14 Pro'),
      ('Schenker XMG Evo 15','Schenker XMG Evo 15 (M24)','laptop','XMG Evo 15'),('Asus Zenbook S 14 UX5406','Asus Zenbook S 14 UX5406','laptop','Zenbook S14'),
      ('Minisforum M2 Pro','Minisforum M2 Pro mini PC','desktop','Minisforum'),('Schenker XMG Neo 16 E25','Schenker XMG Neo 16 E25','laptop','XMG Neo 16'),
      ('Samsung Galaxy Book4 Edge 16','Samsung Galaxy Book4 Edge 16','laptop','Galaxy Book4'),('Dell Pro Max with GB10','Dell Pro Max with GB10','desktop','Dell Pro Max'),
      ('Custom PC','Desktop PC (Core Ultra 7 265K, RTX 4090)','desktop','PC'),('Dell XPS 13','Dell XPS 13 (2026)','laptop','XPS 13')]
def chip(s):
    for k,c,t,sl in CHIPS:
        if s.startswith(k): return c,t,sl
    raise KeyError(s)
def dev(s):
    for k,d,f,sd in DEVS:
        if s.startswith(k): return d,f,sd
    raise KeyError(s)
url2key={v['url']:k for k,v in D['sources'].items()}
def src(r):
    u=r['url']
    if u not in url2key:
        nm=r['src_name'].replace(' results table','').replace(' grouped by device','')
        if '/issues/' in u: nm+=', issue #'+u.rsplit('/',1)[1]
        if 'compute_type=' in u: nm+=' ('+{'CPU':'CPU','HIP':'AMD GPUs, HIP','ONEAPI':'Intel GPUs, oneAPI','OPTIX':'NVIDIA GPUs, OptiX'}[u.split('compute_type=')[1].split('&')[0]]+')'
        k='x86_'+str(len([k for k in D['sources'] if k.startswith('x86_')])); D['sources'][k]=dict(name=nm,url=u); url2key[u]=k
    return url2key[u]
NBC='Notebookcheck measures the whole machine at the wall with an external monitor (internal display off); the bar is the minimum to maximum over the run.'
GEER_PK='Jeff Geerling\'s power column is the peak wall reading during the run, so tokens per joule is a lower bound (as for the M3 Ultra and M4 Mac mini runs from the same project).'
GEER_HPL='Jeff Geerling records average wall power over the run; HPL here runs on the CPU only (BLIS).'
EXTRA={2:'No Cinebench 2024 power was published for this machine: the power is the same review\'s Cinebench R15 multi-core wall power, a sustained all-core load used as a stand-in. Framework configuration 100 W PL1 / 115 W PL2.',
       3:'Thin-and-light, about 28 to 33 W sustained for the chip.',
       4:'Run at its 80 W TDP. The same article sweeps this laptop from 15 to 80 W TDP: 21.3 points per watt at 15 W, 10.2 at 80 W.',
       5:'Performance mode (54 W). In Quiet mode (20 W) the same laptop reaches 20.5 points per watt.',
       6:'Efficiency 13.3 points per watt.',
       12:'No Cinebench 2024 power was published: the power is the same review\'s Cinebench R23 multi-core wall power. A large gaming laptop, so the idle RTX 5090 Laptop GPU is in the reading.',
       29:'No Cinebench 2024 power was published: the power is the same review\'s Cinebench R23 single-core wall power.',
       14:'Native Arm build of Cinebench 2024.',
       35:'Frame rate on Notebookcheck\'s efficiency basis (its 0.562 fps per watt times the wall power), as for the Apple machines.',
       37:'The frame rate is the review\'s 1080p ultra result, which typically runs 5 to 15% above the efficiency-chart basis used for the Apple machines.',
       38:'Frame rate on Notebookcheck\'s efficiency basis, as for the Apple machines.',
       40:'The frame rate is the review\'s 1080p ultra result, which typically runs 5 to 15% above the efficiency-chart basis used for the Apple machines.',
       41:'The frame rate is the review\'s 1080p ultra result, which typically runs 5 to 15% above the efficiency-chart basis used for the Apple machines.',
       42:'Frame rate on Notebookcheck\'s efficiency basis (0.696 fps per watt times 28.6 W); the review itself measured 24.3 fps.',
       44:'Frame rate on Notebookcheck\'s efficiency basis, as for the Apple machines; the review itself measured 49.8 fps.',
       46:'The game runs as an x86 build under Prism emulation on Windows on Arm. The frame rate is the review\'s 1080p ultra result, which typically runs 5 to 15% above the efficiency-chart basis.',
       53:'Discrete-GPU laptop: the wall power covers the RTX 5090 Laptop GPU, the Ryzen AI 9 HX 370 and the rest of the laptop. Frame rate on Notebookcheck\'s efficiency basis.',
       54:'Discrete-GPU laptop at full power (175 W class): the wall power covers the GPU, the Core Ultra 9 275HX and the rest of the laptop. The frame rate is the review\'s 1080p ultra result, typically 5 to 15% above the efficiency-chart basis.',
       58:'Geerling\'s issue #66; 32 cores. The bare mainboard, so no display or chassis fans beyond the cooler.',
       59:'The 20 Arm cores of the GB10 only (no GPU). Two such machines reached 1,333 Gflops at 320 W.',
       60:'The whole desktop at the wall, including the RTX 4090 that is fitted but idle.',
       61:'A laptop, so its own display may be included in the wall power.',
       65:'llama.cpp with Vulkan on the Radeon 8060S; Geerling gives about 133 W.',66:'llama.cpp with Vulkan on the Radeon 8060S; about 133 W.',
       67:'llama.cpp with Vulkan; flash attention was off because it crashed, which likely understates newer builds.',
       68:'Ollama ran on the CPU only here, not the GPU, so this is not a like-for-like GPU run.',
       69:'llama.cpp with CUDA on the Blackwell GPU.',70:'llama.cpp with CUDA.',71:'llama.cpp with CUDA. gpt-oss 120B ran at 52.86 tokens per second at 137.1 W.',72:'llama.cpp with CUDA.',
       73:'llama.cpp with Vulkan, not CUDA. The whole desktop at the wall, including the Core Ultra 7 265K, board and power-supply losses.',
       74:'llama.cpp with Vulkan. Q4_K_M is about 7% larger than the Q4_0 model of the all-chip Llama 2 7B set, so it is not in that set. The whole desktop at the wall.',
       75:'llama.cpp with Vulkan. The whole desktop at the wall.',76:'llama.cpp with Vulkan. The whole desktop at the wall.',
       79:'llama.cpp with Vulkan on the integrated GPU. A laptop.'}
rows=[]; est=[]; by={}
for r in X:
    if r['w'] in ('bl-cpu','bl-gpu'): continue
    c,t,sl=chip(r['chip']); dv,form,sd=dev(r['device']); P=r['p_wall_w']; x=r['x']; e=x/P
    geer='geerlingguy' in r['url']
    q='B' if r.get('approx') or (geer and r['w']=='llm') else 'A'
    note=(GEER_PK if r['w']=='llm' else GEER_HPL if geer else NBC)+(' '+EXTRA[r['id']] if r['id'] in EXTRA else '')
    if r.get('approx'): note='Weaker power figure. '+note
    o=dict(w=r['w'],chip=c,dev=dv,tier=t,form=form,x=x,e=round(e,4),p=P,src=src(r),q=q,bench=r['bench']+(' ('+r['chip'][r['chip'].index('(')+1:-1]+')' if r['w']=='gpu' and '(' in r['chip'] else ''),resc=False,note=note,sl=sl,sd=sd)
    if r.get('p_lo') and r.get('p_hi') and r['p_hi']>r['p_lo']: o.update(plo=r['p_lo'],phi=r['p_hi'],elo=round(x/r['p_hi'],4),ehi=round(x/r['p_lo'],4))
    if r['w']=='llm': o['model']=r['model']
    if r['w']=='gpu': o['game']='Cyberpunk 2077'
    rows.append(o); by[(r['w'],r['device'])]=o
# ---- Blender Open Data medians: power borrowed from a machine on this page, as for the Apple chips
sx=lambda n:0.04+0.15/math.sqrt(n)
def P_of(w,device):
    b=by[(w,device)]; return b,(math.log(b['phi']/b['plo'])/2 if b.get('plo') else 0.1)
BL={80:('cpu-all','Asus ROG Flow Z13 GZ302EA (2025)',''),81:('cpu-all','Asus ProArt P16 H7606WI',''),82:('cpu-all','Schenker VIA 14 Pro (M24)',''),
    83:('cpu-all','Schenker XMG Evo 15 (M24)',''),84:('cpu-all','Asus Zenbook S 14 UX5406',''),86:('cpu-all','Minisforum M2 Pro (mini PC)',''),
    87:('cpu-all','Schenker XMG Neo 16 E25 (RTX 5090 Laptop)','That Cinebench power is itself a stand-in (Cinebench R23 wall power).'),
    92:('hpl','Custom PC (also hosts the RTX 4090 used in the LLM rows)','No Cinebench power exists for this PC, so its HPL wall power stands in; HPL draws 1.1 to 1.4 times the Cinebench power on the Macs that have both, so this point leans pessimistic.'),
    94:('gpu','Asus ROG Flow Z13 GZ302EA (2025)',''),95:('gpu','Asus Zenbook S 16 UM5606',''),
    96:('gpu','Schenker VIA 14 Pro (M24)','The research suggested a lower-power Radeon 780M laptop (Lenovo IdeaPad 5 2-in-1, 51.7 W in Cyberpunk) that is not on this page; this point uses the VIA 14 Pro, the 8845HS machine shown here.'),
    97:('gpu','Asus Zenbook S 14 UX5406',''),99:('gpu','Minisforum M2 Pro (mini PC)',''),105:('gpu','Asus ProArt P16 (RTX 5090)','')}
for r in X:
    if r['w'] not in ('bl-cpu','bl-gpu'): continue
    c,t,sl=chip(r['chip']); n=r['n']; x=r['x']
    if r['id'] in BL:
        pw,device,extra=BL[r['id']]; b,sP=P_of(pw,device); dv,form,sd=b['dev'],b['form'],b['sd']; base=b['p']; weak=bool(extra) and r['id'] in (87,92)
        how=(f"the Cinebench all-core wall power" if pw=='cpu-all' else "the HPL wall power" if pw=='hpl' else "the Cyberpunk 2077 wall power")+f" of the {b['chip']} {dv} ({base:g} W)"
    else:   # RTX 4090 desktop: the only Cyberpunk wall power for this GPU is Notebookcheck's own test PC
        dv,form,sd='Desktop PC with Ryzen 7 9800X3D (Notebookcheck GPU test system)','desktop','NBC test PC'; base=r['p_proxy_w']; sP=0.1; weak=True
        how=f'the Cyberpunk 2077 wall power of Notebookcheck\'s desktop test PC with this GPU and a Ryzen 7 9800X3D ({base:g} W, the whole PC)'
        extra='That PC is not the Geerling desktop whose LLM runs are shown; no range was given for its reading.'
    if r['w']=='bl-cpu': F,sF,fac='1.0',0.095,'0.9 to 1.1 times'
    else: F,sF,fac='0.65',math.log(0.95/0.45)/2,'0.45 to 0.95 (central 0.65) times'
    P=float(F)*base; sxx=sx(n); sp=math.sqrt(sP*sP+sF*sF); s=math.sqrt(sxx*sxx+sp*sp); e=x/P
    note=(f"Render speed measured (Blender Open Data median over every machine with this {'CPU' if r['w']=='bl-cpu' else 'GPU'}, {n} runs, Windows and Linux included); wall power estimated as {fac} {how}, the same rule as for the Apple chips."
          +(' '+extra if extra else '')+' The median mixes chassis and power limits, so it need not match the machine whose power is borrowed.')
    o=dict(w=r['w'],chip=c,ck=c,gen=0,dev=dv+' (estimate)',tier=t,form=form,x=round(x,3),xlo=round(x*math.exp(-sxx),3),xhi=round(x*math.exp(sxx),3),e=round(e,4),elo=round(e*math.exp(-s),4),ehi=round(e*math.exp(s),4),
           p=round(P,1),plo=round(P*math.exp(-sp),1),phi=round(P*math.exp(sp),1),q='B' if weak else 'E',est=1,pe=1,seen=True,src=src(r),resc=False,bench=r['bench'],note=note,sl=sl,sd=sd,grp=c+'|bl',ord=0 if r['w']=='bl-cpu' else 1)
    est.append(o)
D['rows']+=rows; D['est']+=est
json.dump(D,open('data10.json','w'),separators=(',',':'))
for o in rows+est: print(f"{o['w']:7} {o['tier']:8} {o['chip'][:30]:30} {o['dev'][:40]:40} {o.get('model',''):17} x={o['x']:<8} p={o['p']:<6} e={o['e']:<8} q={o['q']}")
