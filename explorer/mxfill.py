"""-> data20.json  Fills empty LLM and Blender cells of the comparison chips in the "same chip, different work" matrix, from
mxfill_rows.json (id = position in that list). LLM: Llama 2 7B Q4_0, llama-bench tg128 (the test of the Apple Silicon thread
that the Apple chips use), on the backend a user of that machine would run: CUDA for NVIDIA (Vulkan where no CUDA row exists),
Vulkan, ROCm or SYCL for AMD and Intel iGPUs, the CPU for the Snapdragon. Blender: Open Data three-scene medians (OptiX for
NVIDIA, oneAPI for Intel; Blender 5.x where Open Data has no 4.5.0 run, said in the note). No power was measured with any of
these runs: every row borrows wall power from a machine already on the page (its LLM, gaming, Cinebench or HPL rows), so every
row is est+pe with a widened range. Cells that stay empty are listed in `gaps` of the rows file with the reason."""
import json, math, statistics
D=json.load(open('data19.json')); J=json.load(open('mxfill_rows.json')); X={r['id']:r for r in J['rows']}
url2key={v['url']:k for k,v in D['sources'].items()}
def src(u,name):
    if u not in url2key:
        k='mx_'+str(len([k for k in D['sources'] if k.startswith('mx_')])); D['sources'][k]=dict(name=name,url=u); url2key[u]=k
    return url2key[u]
def row(w,chip,dev,model=None):
    return next(r for r in D['rows'] if r['w']==w and r['chip']==chip and r['dev']==dev and not r.get('bm') and (model is None or r.get('model')==model))
TIER=lambda c:c.split()[0]
hw=lambda b:math.log(b['phi']/b['plo'])/2 if b.get('plo') else 0.05
EXTRA=0.10   # extra log spread on power for borrowing it from another machine, model or backend
est=[]
def put(r,w,chip,dev,form,sl,sd,x,sx,P,plo,phi,q,bench,note,psrc,model=None,ordv=None):
    e=x/P; o=dict(w=w,chip=chip,ck=chip,gen=0,dev=dev+' (estimate)',tier=TIER(chip),form=form,x=x,xlo=round(x*math.exp(-sx),3),xhi=round(x*math.exp(sx),3),
        e=round(e,4),elo=round(x/phi*math.exp(-sx),4),ehi=round(x/plo*math.exp(sx),4),p=round(P,1),plo=round(plo,1),phi=round(phi,1),
        q=q,est=1,pe=1,seen=True,src=src(r['url'],r['src_name']),psrc=psrc,resc=False,bench=bench,note=note,sl=sl,sd=sd)
    if model: o['model']=model
    if ordv is not None: o.update(grp=chip+'|bl',ord=ordv)
    est.append(o); return o
def sym(P,s): return P,P*math.exp(-s),P*math.exp(s)

# ---------------- LLM: Llama 2 7B Q4_0, tg128 ----------------
L2='Llama 2 7B Q4_0'
LF=math.sqrt(0.75*1.1); LS=math.log(1.1/0.75)/2          # decode wall power = 0.75 to 1.1 times gaming wall power (llm.py, nv2.py)
GAME=('wall power is 0.75 to 1.1 times (central 0.91) the Cyberpunk 2077 wall power of the {dev} ({p:g} W), the rule the page uses for the Macs\' decode power, '
      'widened by 10% because the speed was measured on another machine.')
PEAK=('wall power is 0.75 to 1.05 times (central 0.9) the peak wall reading Jeff Geerling metered on the {dev} running {m} ({p:g} W): '
      'a decode average sits below the peak, and the speed was measured on another machine of the same kind.')
CPUR=('wall power is 0.6 to 1.0 times the Cinebench 2024 all-core wall power of the {dev} ({p:g} W), widened by 10%: generation on the CPU is memory-bound and loads the cores less than Cinebench '
      '(the i9-9880H estimate on this page assumes 55 to 90 W against its 85.2 W Cinebench reading).')
def llm_bench(r): return f"llama.cpp tg128, {r['backend']}{', flash attention' if r['fa'] else ''}; prompt processing {r['pp512']:,.0f} tok/s"
def llm_note(r,how,extra=''):
    return (f"Generation speed measured: llama-bench tg128 with {r['backend']}{' and flash attention' if r['fa'] else ''}, build {r['build']}, on a {r['device']}. "
            f"No power was measured with this run: {how} {r['others']}"+(' '+extra if extra else ''))
def llm_game(i,dev,sx=0.05,q='E',extra=''):
    r=X[i]; b=row('gpu',r['chip'],dev); s=math.sqrt(LS*LS+hw(b)**2+EXTRA**2); P,lo,hi=sym(LF*b['p'],s)
    return put(r,'llm',r['chip'],dev,b['form'],b['sl'],b['sd'],r['x'],sx,P,lo,hi,q,llm_bench(r),llm_note(r,GAME.format(dev=dev,p=b['p']),extra),b['src'],model=L2)
def llm_peak(i,dev,m,sx=0.05,q='E',extra=''):
    r=X[i]; b=row('llm',r['chip'],dev,m); pk=b['p']
    return put(r,'llm',r['chip'],dev,b['form'],b['sl'],b['sd'],r['x'],sx,0.9*pk,0.75*pk,1.05*pk,q,llm_bench(r),llm_note(r,PEAK.format(dev=dev,m=m,p=pk),extra),b['src'],model=L2)
def llm_span(i,devs,label,sd,sx=0.05,q='E',extra=''):
    r=X[i]; bs=[row('gpu',r['chip'],d) for d in devs]; ps=[b['p'] for b in bs]; med=statistics.median(ps)
    how=(f"wall power spans the Cyberpunk 2077 wall power of the {len(bs)} {r['chip'].replace('NVIDIA GeForce ','')} machines on this page ({', '.join(f'{p:g}' for p in ps)} W, whole laptop): "
         f"0.91 times their median ({med:g} W) as the central value, from 0.75 times the lowest to 1.1 times the highest, because the scoreboard does not name the laptop or its power limit.")
    return put(r,'llm',r['chip'],label,'laptop',bs[0]['sl'],sd,r['x'],sx,LF*med,0.75*min(ps),1.1*max(ps),q,llm_bench(r),llm_note(r,how,extra),bs[0]['src'],model=L2)

llm_peak(0,'Framework Desktop mainboard','Llama 3.2 3B',extra='The speed comes from a complete Framework Desktop, the power from Geerling\'s bare mainboard (llama.cpp with Vulkan).')
llm_game(1,'Asus Zenbook S 16 UM5606',extra='The speed comes from a Framework laptop, whose power limit need not match the Zenbook\'s.')
llm_game(2,'Schenker VIA 14 Pro (M24)',sx=0.12,q='B',
         extra='Weaker: the run is on a Ryzen 9 7940HS, the Phoenix chip that the 8845HS (Hawk Point) refreshes with the same Radeon 780M and memory, on an older build and with ROCm rather than Vulkan; 12% speed spread allowed for that.')
llm_game(3,'Asus Zenbook S 14 UX5406',extra='SYCL is Intel\'s backend for its Arc GPUs in mainline llama.cpp; the 2024 Vulkan figure reflects an early driver.')
llm_game(4,'Minisforum M2 Pro mini PC',sx=0.08,q='B',extra='Weaker: one flash-attention run whose CPU model is inferred from the linked machine.')
r=X[5]; b=row('cpu-all',r['chip'],'Samsung Galaxy Book4 Edge 16'); F=math.sqrt(0.6); s=math.sqrt((math.log(1/0.6)/2)**2+hw(b)**2+EXTRA**2); P,lo,hi=sym(F*b['p'],s)
put(r,'llm',r['chip'],b['dev'],b['form'],b['sl'],b['sd'],r['x'],0.08,P,lo,hi,'B',llm_bench(r),
    llm_note(r,CPUR.format(dev=b['dev'],p=b['p']),'Weaker: the laptop\'s chip is the X1E-80-100, a sibling of the X1E-84-100 shown here, and the build is from 2024. The CPU is the backend a Snapdragon user would pick: it is faster here than the Adreno GPU.'),b['src'],model=L2)
llm_peak(6,'Dell Pro Max with GB10','Llama 2 13B',extra='The speed comes from an NVIDIA DGX Spark, the power from the Dell Pro Max with the same GB10 (llama.cpp with CUDA); the larger 13B model may draw a little more than 7B. The DGX Spark points on the LLM tab use an estimated 160 W (120 to 206).')
llm_span(7,['Acer Nitro V 16 (Ryzen 7 8845HS)','Asus ROG Zephyrus G16 GA605WV (Ryzen AI 9 HX 370)','Lenovo LOQ 15IRX9 (Core i5-13450HX)','Lenovo Legion Pro 5 16IRX9 (Core i7-14700HX)'],
         'RTX 4060 Laptop machines on this page','4 laptops',extra='Vulkan, not CUDA: no CUDA row exists for this GPU.')
llm_peak(8,'Desktop PC (Core Ultra 7 265K, RTX 4090)','Llama 2 7B Q4_K_M',extra='Geerling\'s run is the same model at Q4_K_M (about 7% larger) with Vulkan, on the whole desktop at the wall; the CUDA speed comes from another RTX 4090 machine.')
r=X[9]; b=row('gpu',r['chip'],'Desktop PC with Ryzen 7 9800X3D (Notebookcheck GPU test system)'); s=math.sqrt(LS*LS+hw(b)**2+EXTRA**2); P,lo,hi=sym(LF*b['p'],s)
put(r,'llm',r['chip'],b['dev'],b['form'],b['sl'],b['sd'],r['x'],0.05,P,lo,hi,'B',llm_bench(r),
    llm_note(r,GAME.format(dev=b['dev'],p=b['p']),'Weaker: on the RTX 4090, Geerling\'s whole-desktop LLM peak (337.7 W) is 0.62 times Notebookcheck\'s Cyberpunk wall power for that card (549 W, another PC), so the gaming rule likely overstates a desktop\'s decode power and understates this efficiency.'),b['src'],model=L2)
llm_span(10,['Asus ProArt P16 (RTX 5090 Laptop)','Schenker XMG Neo 16 E25','Lenovo Legion 9 18IAX10 (Core Ultra 9 275HX)'],'RTX 5090 Laptop machines on this page','3 laptops')

# ---------------- Blender: Open Data three-scene medians ----------------
sxn=lambda n:0.04+0.15/math.sqrt(n)
def bl_bench(r,dev):
    be='CPU' if r['w']=='bl-cpu' else r['backend']
    return f"Blender {r['blender']} {be}, Open Data median {r['median_spm']:,.2f} samples/min over {r['n']} run{'s' if r['n']>1 else ''} (device \"{dev}\")"
def bl_note(r,how,extra=''):
    n=r['n']
    return (f"Render speed measured (Blender Open Data, {n} run{'s' if n>1 else ''} of the {r['device']} under {r['system']}, three-scene sum, median of runs{f', range {r['min_spm']:,.1f} to {r['max_spm']:,.1f} samples/min' if n>1 else ''}); "
            f"no power is in Open Data: {how} {r['others']}"+(' '+extra if extra else '')+' The median mixes chassis and power limits, so it need not match the machine whose power is borrowed.')
BLC='wall power is 0.9 to 1.1 times {how} ({p:g} W), the same rule as for the Apple chips.'
BLG='wall power is 0.45 to 0.95 (central 0.65) times {how} ({p:g} W), the same rule as for the Apple chips.'
SG=math.log(0.95/0.45)/2
V5='Blender {v} rather than the 4.5.0 of most points: in the same snapshot {cmp}, so a further {pct:.0f}% speed spread is allowed.'
# N1X CPU: Blender 5.2.0, power from the Surface Laptop Ultra's Cinebench all-core wall power
r=X[11]; b=row('cpu-all',r['chip'],'Microsoft Surface Laptop Ultra (2026)'); x=round(r['median_spm']/60,3); sv=0.07
s=math.sqrt(0.095**2+hw(b)**2); P,lo,hi=sym(b['p'],s)
put(r,'bl-cpu',r['chip'],b['dev'],b['form'],b['sl'],b['sd'],x,math.sqrt(sxn(r['n'])**2+sv*sv),P,lo,hi,'B',bl_bench(r,r['device']),
    bl_note(r,BLC.format(how='the Cinebench all-core wall power of the Surface Laptop Ultra (2026)',p=b['p']),
            V5.format(v='5.2.0 LTS',cmp='5.2.0 CPU medians run 1% (Core Ultra 7 265K) to 14% (Core Ultra 9 275HX) above 4.5.0',pct=sv*100)+' The ProArt P16 with the same chip draws 127.1 W in Cinebench.'),b['src'],ordv=0)
# Core 5 320 CPU: Blender 5.2.0, two runs; power from the Dell XPS 13's HPL wall power (no Cinebench power exists for it)
r=X[12]; b=row('hpl',r['chip'],'Dell XPS 13 (2026)'); x=round(r['median_spm']/60,3)
s=math.sqrt(0.095**2+0.1**2+EXTRA**2); P,lo,hi=sym(b['p'],s)
put(r,'bl-cpu',r['chip'],b['dev'],b['form'],b['sl'],b['sd'],x,math.sqrt(sxn(r['n'])**2+sv*sv),P,lo,hi,'B',bl_bench(r,r['device']),
    bl_note(r,BLC.format(how='the HPL wall power of the Dell XPS 13 (2026) (a CPU-only load; no Cinebench power exists for this laptop)',p=b['p']),
            'Weaker: two runs. '+V5.format(v='5.2.0 LTS',cmp='5.2.0 CPU medians run 1% to 14% above 4.5.0',pct=sv*100)
            +' HPL draws 1.1 to 1.4 times the Cinebench power on the Macs that have both, so this point leans pessimistic; 10% more power spread is allowed for that.'),b['src'],ordv=0)
# RTX 4060 Laptop GPU: span of the four RTX 4060 Laptop machines' Cyberpunk wall power
r=X[13]; devs=['Acer Nitro V 16 (Ryzen 7 8845HS)','Asus ROG Zephyrus G16 GA605WV (Ryzen AI 9 HX 370)','Lenovo LOQ 15IRX9 (Core i5-13450HX)','Lenovo Legion Pro 5 16IRX9 (Core i7-14700HX)']
bs=[row('gpu',r['chip'],d) for d in devs]; ps=[q['p'] for q in bs]; med=statistics.median(ps); x=round(r['median_spm']/60,3)
how=(f"wall power spans the Cyberpunk 2077 wall power of the four RTX 4060 Laptop machines on this page ({', '.join(f'{p:g}' for p in ps)} W, whole laptop): 0.65 times their median ({med:g} W) as the central value, "
     "from 0.45 times the lowest to 0.95 times the highest, the Apple chips' render rule stretched over machines whose GPU power limits run from 80 to 140 W.")
put(r,'bl-gpu',r['chip'],'RTX 4060 Laptop machines on this page','laptop',bs[0]['sl'],'4 laptops',x,sxn(r['n']),0.65*med,0.45*min(ps),0.95*max(ps),'E',bl_bench(r,r['device']),bl_note(r,how),bs[0]['src'],ordv=1)
# RTX 5090 desktop: Notebookcheck's test PC with this card
r=X[14]; b=row('gpu',r['chip'],'Desktop PC with Ryzen 7 9800X3D (Notebookcheck GPU test system)'); x=round(r['median_spm']/60,3)
s=math.sqrt(SG*SG+hw(b)**2); P,lo,hi=sym(0.65*b['p'],s)
put(r,'bl-gpu',r['chip'],b['dev'],b['form'],b['sl'],b['sd'],x,sxn(r['n']),P,lo,hi,'E',bl_bench(r,r['device']),
    bl_note(r,BLG.format(how='the Cyberpunk 2077 wall power of Notebookcheck\'s test PC with this card and a Ryzen 7 9800X3D (the whole PC)',p=b['p'])),b['src'],ordv=1)
# N1X GPU: Blender 5.3.0, power from the Surface Laptop Ultra's Cyberpunk wall power
r=X[15]; b=row('gpu',r['chip'],'Microsoft Surface Laptop Ultra (2026)'); x=round(r['median_spm']/60,3); sv=0.2
s=math.sqrt(SG*SG+0.05**2); P,lo,hi=sym(0.65*b['p'],s)
put(r,'bl-gpu',r['chip'],b['dev'],b['form'],b['sl'],b['sd'],x,math.sqrt(sxn(r['n'])**2+sv*sv),P,lo,hi,'B',bl_bench(r,r['device']),
    bl_note(r,BLG.format(how='the Cyberpunk 2077 wall power of the Surface Laptop Ultra (2026)',p=b['p']),'Weaker: Blender 5.3.0, so a further 20% speed spread is allowed.'),b['src'],ordv=1)
# Core 5 320 iGPU: one Blender 5.2.0 run; power between the XPS 13's two measured loads
r=X[16]; lo_=row('llm',r['chip'],'Dell XPS 13 (2026)','Llama 3.2 3B'); hi_=row('hpl',r['chip'],'Dell XPS 13 (2026)'); x=round(r['median_spm']/60,3)
P=math.sqrt(lo_['p']*hi_['p'])
how=(f"wall power is taken between the Dell XPS 13 (2026)'s two measured loads, {lo_['p']:g} W (Geerling's peak with llama.cpp on this iGPU, a memory-bound load that rendering should exceed) and "
     f"{hi_['p']:g} W (HPL on the CPU, a sustained load at the chip's power limit), central {P:.1f} W (their geometric mean).")
put(r,'bl-gpu',r['chip'],lo_['dev'],lo_['form'],lo_['sl'],lo_['sd'],x,math.sqrt(sxn(1)**2+0.07**2),P,lo_['p'],hi_['p'],'B',bl_bench(r,'Intel(R) Graphics'),
    bl_note(r,how,'Weaker: one run, on Blender 5.2.0 LTS rather than 4.5.0.'),lo_['src'],ordv=1)

# every target cell must have been empty before this step
for o in est:
    k=o['w']; m=lambda q:q['w']==k and q['ck' if 'ck' in q else 'chip']==o['chip'] and not q.get('srv') and not q.get('bm') and not q.get('mode') and (k!='llm' or q.get('model')==L2)
    assert not any(m(q) for q in D['rows']+D['est']), ('cell already filled',k,o['chip'])
used={i for i in X}; assert len(est)==len(used)==17
D['est']+=est
json.dump(D,open('data20.json','w'),separators=(',',':'))
for o in est: print(f"{o['w']:6} {o['chip'][:32]:32} {o['dev'][:44]:44} x={o['x']:<8} [{o['xlo']},{o['xhi']}] p={o['p']:<6} [{o['plo']},{o['phi']}] e={o['e']:<8} [{o['elo']},{o['ehi']}] q={o['q']}")
print('gaps:'); [print('  ',k) for k in J['gaps']]
