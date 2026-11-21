"""-> data14.json  NVIDIA additions and comparison-chip gaps, from nv2_rows.json (each row with the URL that was read):
Dell Pro Max with GB10 LLM runs with Geerling's wall power; DGX Spark speed-only LLM runs with an estimated ~160 W; RTX 4060
laptops (four Notebookcheck machines) and an RTX 4060 desktop (KitGuru, whole PC at the wall); RTX 5090 desktop (Notebookcheck
test PC); RTX 5090 Laptop Legion 9 (Cyberpunk measured, LLM power estimated); RTX 4090 desktop Cyberpunk; NVIDIA N1X (RTX Spark)
laptops as a comparison chip in their own right; and Blender Open Data medians for the Snapdragon X Elite CPU, the 155H's Arc
iGPU, the RTX 4060 desktop and the GB10's CPU (one Windows run). The conventions are those of x86.py: the chip is the
component doing the work, the power is the whole machine at the wall. Rows whose power is not of the same run are est+pe."""
import json, math
D=json.load(open('data13.json')); X={r['id']:r for r in json.load(open('nv2_rows.json'))['rows']}
url2key={v['url']:k for k,v in D['sources'].items()}
def src(u,name):
    if u not in url2key:
        k='nv2_'+str(len([k for k in D['sources'] if k.startswith('nv2_')])); D['sources'][k]=dict(name=name,url=u); url2key[u]=k
    return url2key[u]
NBC='Notebookcheck measures the whole machine at the wall with an external monitor (internal display off), averaged over the run.'
REV='The frame rate is the review\'s 1080p ultra result, which typically runs 5 to 15% above the efficiency-chart basis used for the Apple machines.'
GEER_PK='Jeff Geerling\'s power column is the peak wall reading during the run, so tokens per joule is a lower bound (as for the M3 Ultra and M4 Mac mini runs from the same project).'
rows=[]; est=[]
def put(o,measured):
    (rows if measured else est).append(o); return o
def base(r,w,chip,dev,form,sl,sd,x,bench,note,q,model=None,game=None,srcname=None):
    o=dict(w=w,chip=chip,dev=dev,tier='NVIDIA' if chip.startswith('NVIDIA') else chip.split()[0],form=form,x=x,src=src(r['url'],srcname or r['src_name']),q=q,bench=bench,resc=False,note=note,sl=sl,sd=sd)
    if model: o['model']=model
    if w=='gpu': o['game']=game or 'Cyberpunk 2077'
    return o
def measured(r,w,chip,dev,form,sl,sd,note,q='A',bench=None,model=None,x=None,srcname=None):
    x=x or r['x']; P=r['p_wall_w']; o=base(r,w,chip,dev,form,sl,sd,x,bench or r['bench'],note,q,model,srcname=srcname)
    o.update(e=round(x/P,4),p=P)
    if r.get('p_lo') and r.get('p_hi') and r['p_hi']>r['p_lo']: o.update(plo=r['p_lo'],phi=r['p_hi'],elo=round(x/r['p_hi'],4),ehi=round(x/r['p_lo'],4))
    return put(o,True)
def estimated(r,w,chip,dev,form,sl,sd,P,sP,sx,note,q='E',bench=None,model=None,game=None,grp=None,ordv=None,psrc=None,srcname=None):
    x=r['x']; s=math.sqrt(sP*sP+sx*sx); e=x/P
    o=base(r,w,chip,dev,form,sl,sd,x,bench or r['bench'],note,q,model,game,srcname)
    o.update(ck=chip,gen=0,xlo=round(x*math.exp(-sx),3),xhi=round(x*math.exp(sx),3),e=round(e,4),elo=round(e*math.exp(-s),4),ehi=round(e*math.exp(s),4),
             p=round(P,1),plo=round(P*math.exp(-sP),1),phi=round(P*math.exp(sP),1),est=1,pe=1,seen=True)
    if grp: o.update(grp=grp,ord=ordv)
    if psrc: o['psrc']=psrc
    return put(o,False)
def ranged(r,w,chip,dev,form,sl,sd,P,plo,phi,sx,note,q='E',bench=None,model=None,psrc=None,srcname=None):
    """an estimate with an explicit, asymmetric power range"""
    x=r['x']; e=x/P; o=base(r,w,chip,dev,form,sl,sd,x,bench or r['bench'],note,q,model,srcname=srcname)
    o.update(ck=chip,gen=0,xlo=round(x*math.exp(-sx),3),xhi=round(x*math.exp(sx),3),e=round(e,4),elo=round(x/phi*math.exp(-sx),4),ehi=round(x/plo*math.exp(sx),4),
             p=P,plo=plo,phi=phi,est=1,pe=1,seen=True)
    if psrc: o['psrc']=psrc
    return put(o,False)
row=lambda w,chip,dev: next(r for r in D['rows'] if r['w']==w and r['chip']==chip and r['dev']==dev)

# ---- NVIDIA GB10: four more Geerling runs on the Dell Pro Max with GB10 (same box as the rows already on the page)
GB='NVIDIA GB10'; DELL='Dell Pro Max with GB10'
for i,model,extra in ((19,'gpt-oss 120B','The model file is labelled Q4_K_M in the table; gpt-oss is natively MXFP4.'),
                      (20,'Qwen3 32B','The table label mentions Qwen3 30B-A3B, but 10.46 tokens per second matches the dense Qwen3 32B (the 30B-A3B mixture of experts runs at about 89 on GB10).'),
                      (21,'Llama 2 13B',''),(22,'Llama 3.3 70B','Llama 3.1 70B on the same machine ran at 4.71 tokens per second at 154.9 W.')):
    r=X[i]; measured(r,'llm',GB,DELL,'desktop','GB10','Dell Pro Max',GEER_PK+' llama.cpp with CUDA on the Blackwell GPU. '+extra,q='B',bench=r['bench'],model=model,
                     srcname='Jeff Geerling, ai-benchmarks (llama.cpp/Ollama) results, issue #34')
# ---- NVIDIA DGX Spark (GB10): speed-only runs; power estimated from the ~160 W wall readings under LLM and GPU load
SPARK_P,SPARK_LO,SPARK_HI=160.0,120.0,206.0
SPARK=('No wall power was measured with these runs. Power is estimated at 160 W, the wall reading Tom\'s Hardware gives for the DGX Spark under a mainly GPU-driven load and Notebookcheck for the HP ZGX Nano G1n (the same GB10 hardware) in sustained LLM inference; '
       'the range runs from 120 W (just below the 122.8 to 156 W peaks Jeff Geerling metered on the Dell Pro Max with GB10 across models) to 206 W (Notebookcheck\'s maximum). '
       'Geerling\'s peaks sit below 160 W, so these points more likely understate the efficiency than overstate it. The Spark idles at 35 to 45 W, so short runs fare worse than long ones.')
for i,model,q,extra in ((26,'gpt-oss 20B (Ollama)','E','Ollama, MXFP4, as tested by LMSYS; the same model under llama.cpp runs about 1.7 times faster on GB10 (82.7 to 88 tokens per second), so the engine matters as much as the chip.'),
                        (27,'Llama 3.1 8B FP8 (SGLang)','E','SGLang at batch size 1, FP8, as tested by LMSYS (368 tokens per second in all at batch 32).'),
                        (28,'Qwen3 8B','E','llama.cpp (llama-bench), Q4_K_M, 512-token context (42.0 at 2,048), from a community report on GitHub.'),
                        (29,'Qwen3 30B-A3B','E','llama.cpp (llama-bench), Q4_K_M, a mixture of experts with about 3B active parameters, 512-token context (83.8 at 2,048), from a community report on GitHub.'),
                        (30,'gpt-oss 120B','B','llama.cpp build 6816, MXFP4, tg32 at empty context (34.3 at 32k), from a community table in llama.cpp discussion #16578, read through a summary; build 6922 reached 60.6. Weaker: read from a summary.')):
    r=X[i]; ranged(r,'llm',GB,'NVIDIA DGX Spark','desktop','GB10','DGX Spark',SPARK_P,SPARK_LO,SPARK_HI,0.05,'Generation speed measured: '+extra+' '+SPARK,q=q,bench=r['bench'],model=model,
           psrc=src(X[23]['url'],'Notebookcheck, HP ZGX Nano G1n (GB10) review (power under LLM load)'))
# ---- RTX 4060 Laptop: four Notebookcheck machines (the most efficient, an HX 370 thin laptop, a mass-market one, a high-power one)
L4='NVIDIA GeForce RTX 4060 Laptop'
for i,dev,sd,cpu,tgp,q,extra in ((0,'Acer Nitro V 16 (Ryzen 7 8845HS)','Nitro V 16','Ryzen 7 8845HS',85,'A','The most efficient RTX 4060 laptop in Notebookcheck\'s list.'),
                                 (1,'Asus ROG Zephyrus G16 GA605WV (Ryzen AI 9 HX 370)','Zephyrus G16','Ryzen AI 9 HX 370',80,'A',''),
                                 (11,'Lenovo LOQ 15IRX9 (Core i5-13450HX)','LOQ 15','Core i5-13450HX',115,'B','Weaker: the frame rate is the review table\'s balanced-mode value (78.5 fps in performance mode), and the review does not say which mode the 150.9 W power run used (155.7 W with the internal display).'),
                                 (9,'Lenovo Legion Pro 5 16IRX9 (Core i7-14700HX)','Legion Pro 5','Core i7-14700HX',140,'A','A high-power configuration: about 10% more frames than the Nitro V 16 for almost twice the wall power.')):
    r=X[i]; measured(r,'gpu',L4,dev,'laptop','RTX 4060 Laptop',sd,f'Discrete-GPU laptop: the wall power covers the RTX 4060 Laptop GPU ({tgp} W TGP), the {cpu} and the rest of the laptop. '+NBC+' '+REV+(' '+extra if extra else ''),q=q,
             bench=f'Cyberpunk 2077, 1080p ultra, FSR off ({cpu})',srcname='Notebookcheck, '+('RTX 4060 Laptop GPU page (per-review data)' if i!=11 else 'Lenovo LOQ 15 review'))
# ---- RTX 4060 desktop (KitGuru, whole test PC with a Core i9-13900KS at the wall)
D4='NVIDIA GeForce RTX 4060'; KG='Desktop PC (Core i9-13900KS, RTX 4060; KitGuru test system)'
r=X[13]; c4060=measured(r,'gpu',D4,KG,'desktop','RTX 4060','KitGuru PC',
    'Weaker power figure: KitGuru\'s total system power at the wall over 30 minutes of Cyberpunk at 1080p, read from a chart; the text says it "peaked at just over 320 W", so 323 W may be a peak rather than an average. '
    'The whole desktop is measured, so the 13900KS, board and power supply dominate: KitGuru\'s card-only reading is about 125 W, which would give 0.58 frames per joule for the card alone. The frame rate is KitGuru\'s 1080p ultra average (DLSS and FSR off), on its own rig.',
    q='B',bench='Cyberpunk 2077, 1080p ultra, DLSS and FSR off (KitGuru, whole PC)',srcname='KitGuru, MSI RTX 4060 Ventus 2X review')
# ---- RTX 5090 desktop (Notebookcheck test PC with a Ryzen 7 9800X3D; the whole PC at the wall in its Cyberpunk FHD run)
D5='NVIDIA GeForce RTX 5090'; NBCPC='Desktop PC with Ryzen 7 9800X3D (Notebookcheck GPU test system)'
r=X[16]; measured(r,'gpu',D5,NBCPC,'desktop','RTX 5090','NBC test PC',
    'Weaker: the wall power (636 W, 616 to 647, the whole PC) is Notebookcheck\'s Cyberpunk 2077 FHD ultra run, but the 220 fps is inferred from a sparse table whose 4K value matches the 4K chart. KitGuru measured 237.2 fps at the same settings on its own rig; its power for this card is card-only (421.5 W, a 12-game average), not the wall, so it is not used. Cyberpunk at 1080p is partly CPU-limited on this card.',
    q='B',bench='Cyberpunk 2077, 1080p ultra, FSR off (Notebookcheck, whole PC)',srcname='Notebookcheck, GeForce RTX 5090 Founders Edition review')
# ---- RTX 4090 desktop: KitGuru frame rate, wall power of Notebookcheck's test PC with this card in the same test
G4='NVIDIA GeForce RTX 4090'; r=X[18]
o=estimated(r,'gpu',G4,NBCPC,'desktop','RTX 4090','NBC test PC',549.0,math.sqrt((math.log(554/540)/2)**2+0.12**2),0.03,
    'Frame rate measured by KitGuru (1080p ultra, DLSS and FSR off) on its own test rig; Notebookcheck gives no 1080p frame rate for this card. Wall power is estimated from Notebookcheck\'s test PC with this card (Ryzen 7 9800X3D) in its Cyberpunk 2077 FHD ultra run, 549 W (540 to 554, the whole PC), widened by 12% because the two rigs differ. '
    'KitGuru\'s card-only power (325.8 W, a 12-game average) is not wall power and is not used. This is not the Geerling desktop whose LLM runs are shown.',
    q='B',bench='Cyberpunk 2077, 1080p ultra, DLSS and FSR off (KitGuru frame rate)',game='Cyberpunk 2077',psrc=src(X[16]['url'],'Notebookcheck, GeForce RTX 5090 Founders Edition review'),srcname='KitGuru, RTX 5090 review (RTX 4090 Founders Edition result)')
# ---- RTX 5090 Laptop: Lenovo Legion 9 (Cyberpunk measured; MLPerf Client LLM speed with power estimated)
L5='NVIDIA GeForce RTX 5090 Laptop'; LEG='Lenovo Legion 9 18IAX10 (Core Ultra 9 275HX)'
r=X[40]; leg=measured(r,'gpu',L5,LEG,'laptop','RTX 5090 Laptop','Legion 9',
    'Discrete-GPU laptop with the GPU overclocked, the highest-power RTX 5090 Laptop machine Notebookcheck has tested: the wall power covers the GPU, the Core Ultra 9 275HX and the rest of the laptop. '+NBC+' '+REV,
    bench='Cyberpunk 2077, 1080p ultra, FSR off (Core Ultra 9 275HX)',srcname='Notebookcheck, Lenovo Legion 9 18 RTX 5090 review')
LF=math.sqrt(0.75*1.1); LS=math.log(1.1/0.75)/2   # LLM decode power as a fraction of GPU-load wall power, as for the Macs
def llm_est(r,chip,dev,sl,sd,cp,extra):
    P=LF*cp['p']; hw=math.log(cp['phi']/cp['plo'])/2 if cp.get('plo') else 0.05
    return estimated(r,'llm',chip,dev,'laptop',sl,sd,P,math.sqrt(LS*LS+hw*hw),0.03,
        f"Generation speed measured: Notebookcheck's MLPerf Client 2.0 run on the GPU (Llama 3.1 8B; quantisation and engine set by MLPerf Client, not stated). No power was measured with it: wall power is 0.75 to 1.1 times (central {LF:.2f}) this laptop's Cyberpunk 2077 wall power ({cp['p']:g} W), the rule the page uses for the Macs' decode power. "
        "The research treats the gaming power as an upper bound for LLM decode, so this efficiency is more likely understated. "+extra,
        q='B',bench='MLPerf Client 2.0, GPU, Llama 3.1 8B',model='Llama 3.1 8B (MLPerf Client)',psrc=cp['src'],srcname='Notebookcheck, RTX Spark analysis (MLPerf Client 2.0 chart)')
llm_est(X[39],L5,LEG,'RTX 5090 Laptop','Legion 9',leg,'Qwen3 8B ran at 119 tokens per second in the same chart.')
# ---- NVIDIA N1X (RTX Spark): a Windows-on-Arm laptop SoC (20 Arm cores, Blackwell GPU), its own comparison chip
N1='NVIDIA N1X (RTX Spark)'
N1N=('The N1X (RTX Spark) is a Windows-on-Arm laptop SoC with 20 Arm cores and a 6,144-core Blackwell GPU, related to the GB10 but a different chip (about 80 W in laptops). '+NBC)
PA,SU='Asus ProArt P16 H7607 (RTX Spark)','Microsoft Surface Laptop Ultra (2026)'
n1={}
for i,w,dev,sd,extra in ((32,'cpu-all',PA,'ProArt P16',''),(33,'cpu-one',PA,'ProArt P16','The single-thread power range is wide (20.9 to 70 W).'),(34,'gpu',PA,'ProArt P16','Cyberpunk runs as an x64 build under emulation on Windows on Arm; the frame rate is on Notebookcheck\'s efficiency basis (its chart gives 0.585 fps per watt).'),
                         (35,'cpu-all',SU,'Surface Ultra',''),(36,'cpu-one',SU,'Surface Ultra',''),(37,'gpu',SU,'Surface Ultra','Cyberpunk runs as an x64 build under emulation on Windows on Arm; the frame rate is on Notebookcheck\'s efficiency basis (its chart gives 0.654 fps per watt).')):
    r=X[i]; nm='Notebookcheck, '+('Asus ProArt P16 RTX Spark review' if dev==PA else 'Microsoft Surface Laptop Ultra RTX Spark review')
    bench={'cpu-all':'Cinebench 2024','cpu-one':'Cinebench 2024','gpu':'Cyberpunk 2077, 1080p ultra, FSR off (x64 emulation)'}[w]
    n1[(w,dev)]=measured(r,w,N1,dev,'laptop','N1X',sd,N1N+(' '+extra if extra else ''),bench=bench,srcname=nm)
llm_est(X[38],N1,SU,'N1X','Surface Ultra',n1[('gpu',SU)],'The ProArt P16 with the same chip ran at 55.8 tokens per second; Qwen3 8B ran at 54.8 and 53.8.')
# ---- Blender Open Data medians: power borrowed from a machine on this page, as in x86.py
sxn=lambda n:0.04+0.15/math.sqrt(n)
def blender(r,w,chip,dev,sl,sd,b,how,q,extra,grp=None,ordv=None,bench=None):
    if w=='bl-cpu': F,sF,fac=1.0,0.095,'0.9 to 1.1 times'
    else: F,sF,fac=0.65,math.log(0.95/0.45)/2,'0.45 to 0.95 (central 0.65) times'
    sP=math.log(b['phi']/b['plo'])/2 if b.get('plo') else 0.1; n=r['n']
    note=(f"Render speed measured (Blender Open Data, {n} run{'s' if n>1 else ''}); wall power estimated as {fac} {how} ({b['p']:g} W), the same rule as for the Apple chips. "+extra
          +' The median mixes chassis and power limits, so it need not match the machine whose power is borrowed.')
    return estimated(r,w,chip,dev+' (estimate)',b['form'],sl,sd,F*b['p'],math.sqrt(sP*sP+sF*sF),sxn(n),note,q=q,bench=bench or r['bench'],grp=grp,ordv=ordv,srcname='Blender Open Data snapshot (Blender 4.5.0 unless noted)')
xe=row('cpu-all','Qualcomm Snapdragon X Elite X1E-84-100','Samsung Galaxy Book4 Edge 16')
blender(X[43],'bl-cpu','Qualcomm Snapdragon X Elite X1E-84-100','Samsung Galaxy Book4 Edge 16','X Elite','Galaxy Book4',xe,'the Cinebench all-core wall power of the Galaxy Book4 Edge 16',
        'B','Weaker: Open Data has one run for the X1E-84-100. Sibling chips agree within about 4%: the X1E-78-100 has 4.436 samples per second over 4 runs and the X1E-80-100 4.272 over 9 (a second X1E-80-100 device name gives 3.382 over 5).')
ev=row('gpu','Intel Core Ultra 7 155H','Schenker XMG Evo 15 (M24)')
blender(X[45],'bl-gpu','Intel Core Ultra 7 155H','Schenker XMG Evo 15 (M24)','155H','XMG Evo 15',ev,'the Cyberpunk 2077 wall power (run on this iGPU) of the XMG Evo 15 (M24)',
        'E','Open Data names this GPU "Intel(R) Arc(TM) Graphics" for several Meteor Lake and Arrow Lake chips, so runs were kept only where the CPU is the 155H (Windows).',grp='Intel Core Ultra 7 155H|bl',ordv=1)
blender(X[15],'bl-gpu',D4,KG,'RTX 4060','KitGuru PC',c4060,'the Cyberpunk 2077 wall power of the KitGuru RTX 4060 desktop (the whole PC)',
        'B','Weaker: that power reading is itself a chart value that may be a peak. Windows runs give a median of 52.1 samples per second, Linux 53.7.')
gbh=row('hpl',GB,DELL)
blender(X[31],'bl-cpu',GB,DELL,'GB10','Dell Pro Max',gbh,'the HPL wall power of the Dell Pro Max with GB10 (a CPU-only load on the same 20 Arm cores; no Cinebench power exists for GB10)',
        'B','Weaker: the only GB10 entry in Open Data is one run under Windows on Arm with Blender 5.2.0, not the 4.5.0 used for every other point, on an unnamed machine reporting "GB10" with 20 cores (the GB10 machines on this page run Linux). HPL draws 1.1 to 1.4 times the Cinebench power on the Macs that have both, so this point leans pessimistic.',
        bench='Blender 5.2.0 CPU, Open Data, one run (Windows on Arm, device "GB10"), three-scene sum 405.39 samples per minute')
D['rows']+=rows; D['est']+=est
json.dump(D,open('data14.json','w'),separators=(',',':'))
for o in rows+est: print(f"{o['w']:7} {o['chip'][:30]:30} {o['dev'][:44]:44} {o.get('model',''):26} x={o['x']:<8} p={o['p']:<6} [{o.get('plo','')},{o.get('phi','')}] e={o['e']:<8} q={o['q']} {'pe' if o.get('pe') else ''}")
