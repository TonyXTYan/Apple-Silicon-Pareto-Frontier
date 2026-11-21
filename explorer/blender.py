import json, math
D=json.load(open('data3.json'))
for r in D['est']:
    if r['w']=='llm' and r.get('src')=='llamacpp': r['pe']=1
# Blender Open Data, Blender 4.5.0 medians (samples per minute; sum over monster, junkshop, classroom), (score, n)
CPU={'M1':(95.36,105),'M1 Pro':(177.02,63),'M1 Max':(210.55,50),'M1 Ultra':(433.50,11),'M2':(111.26,63),'M2 Pro':(205.79,40),'M2 Max':(260.61,37),'M2 Ultra':(525.96,11),
     'M3':(125.56,49),'M3 Pro':(226.36,45),'M3 Max':(401.62,52),'M3 Ultra':(716.44,27),'M4':(223.54,258),'M4 Pro':(343.55,170),'M4 Max':(470.08,134),
     'M5':(275.07,48),'M5 Pro':(535.63,6),'M5 Max':(604.99,7),'M5 Ultra':(1012.61,1),'M6':(352.91,3)}
GPU={'M1':(8,260.37,27),'M1 Pro':(16,483.45,44),'M1 Max':(32,955.45,50),'M1 Ultra':(64,1656.68,6),'M2':(10,353.39,12),'M2 Pro':(19,901.98,12),'M2 Max':(38,1797.98,25),'M2 Ultra':(76,3407.67,4),
     'M3':(10,914.80,18),'M3 Pro':(18,1756.38,30),'M3 Max':(40,4263.07,41),'M3 Ultra':(80,7431.22,7),'M4':(10,1080.60,176),'M4 Pro':(20,2568.39,123),'M4 Max':(40,5266.87,124),
     'M5':(10,1734.16,33),'M5 Pro':(20,3673.15,3),'M5 Max':(40,7065.02,6),'M5 Ultra':(64,11344.78,1),'M6':(12,2490.43,3)}
# Per-scene medians, Blender 4.5.0, from the full Open Data snapshot (opendata-latest.zip, 2026-11-21): (runs, monster, junkshop, classroom) in samples/min.
# The scene rows reuse the power of the three-scene row; the three-scene score above stays the published per-chip median of the summed score.
SCENES=('monster','junkshop','classroom')
SCPU={'M1':(105,61.48,5.1,27.0),'M1 Pro':(63,91.67,48.87,38.84),'M1 Max':(50,101.41,63.84,45.54),'M1 Ultra':(11,208.32,131.29,93.3),'M2':(63,67.82,10.21,31.66),'M2 Pro':(40,97.71,63.73,44.75),'M2 Max':(37,124.9,78.96,56.94),'M2 Ultra':(11,249.85,160.47,115.35),'M3':(49,79.29,14.47,34.42),'M3 Pro':(45,107.69,69.61,49.86),'M3 Max':(52,197.21,119.53,86.13),'M3 Ultra':(27,345.27,214.97,156.59),'M4':(258,109.13,67.82,47.32),'M4 Pro':(170,165.88,103.78,74.74),'M4 Max':(134,227.57,141.43,100.08),'M5':(48,131.58,84.98,58.88),'M5 Pro':(6,261.87,163.23,110.38),'M5 Max':(7,293.65,181.87,129.47),'M5 Ultra':(1,489.05,302.87,220.69),'M6':(3,169.34,107.73,75.62)}
SGPU={('M1',8):(27,130.22,66.58,65.61),('M1 Pro',16):(44,238.86,127.5,116.22),('M1 Max',32):(50,469.29,260.21,227.48),('M1 Ultra',64):(6,807.46,443.99,405.56),('M2',10):(12,175.61,87.33,87.23),('M2 Pro',19):(12,432.31,248.86,220.93),('M2 Max',38):(25,853.45,514.78,431.78),('M2 Ultra',76):(4,1618.8,969.54,817.53),('M3',10):(18,442.84,222.3,248.45),('M3 Pro',18):(30,887.3,416.44,453.04),('M3 Max',40):(41,2045.02,1127.89,1091.25),('M3 Ultra',80):(7,3632.43,1874.69,1914.41),('M4',10):(176,535.89,244.96,301.7),('M4 Pro',20):(123,1244.42,648.61,673.66),('M4 Max',40):(124,2514.25,1396.7,1346.87),('M5',10):(33,833.38,428.23,475.28),('M5 Pro',20):(3,1739.4,983.25,945.07),('M5 Max',40):(6,3360.99,2013.63,1690.53),('M5 Ultra',64):(1,5393.78,3195.54,2755.45),('M6',12):(3,1209.64,614.88,665.91),('M2',8):(11,150.44,75.8,74.28)}
FEW=3   # medians over this many runs or fewer are flagged as weaker measurements (q='B')
TIER=lambda c:'Ultra' if 'Ultra' in c else 'Max' if 'Max' in c else 'Pro' if 'Pro' in c else 'base'
ck=lambda c:c.rsplit(' ',1)[0] if c.endswith('c') and c.split()[-1][:-1].isdigit() else c
sx=lambda n:0.04+0.15/math.sqrt(n)       # log-sd of a chip median: chassis and config mix, plus sampling
def mk(w,c,dev,form,x,P,slogP,sF,sxx,bench,note,n,scene=None):
    if n<=FEW: note+=f' Only {n} run'+('s' if n>1 else '')+' in Open Data, so this median is a weak measurement.'
    e=x/P; s=math.sqrt(sxx**2+slogP**2+sF**2); sp=math.sqrt(slogP**2+sF**2)
    return dict(w=w,chip=c,ck=c,gen=int(c[1]),dev=dev+' (estimate)',tier=TIER(c),form=form,x=round(x,2),xlo=round(x*math.exp(-sxx),2),xhi=round(x*math.exp(sxx),2),
        e=round(e,4),elo=round(e*math.exp(-s),4),ehi=round(e*math.exp(s),4),p=round(P,1),plo=round(P*math.exp(-sp),1),phi=round(P*math.exp(sp),1),
        q='B' if n<=FEW else 'E',est=1,pe=1,seen=True,src='blender',resc=False,bench=bench,note=note,grp=c+'|bl'+('|'+scene if scene else ''),ord=0 if w=='bl-cpu' else 1,**({'scene':scene} if scene else {}))
rows=[]
# ---- CPU: power = 1.0 (0.9 to 1.1) x the same machine's Cinebench all-core wall power
ca=[r for r in D['rows'] if r['w']=='cpu-all']; ce=[r for r in D['est'] if r['w']=='cpu-all' and not r.get('mode')]
def pick(c):
    m=[r for r in ca if ck(r['chip'])==c]
    if m:
        for pref in (lambda r:r['dev']=='Mac mini',lambda r:r['dev']=='Mac Studio',lambda r:r['form']=='laptop',lambda r:True):
            q=[r for r in m if pref(r)]
            if q: return max(q,key=lambda r:r['x']),False
    q=[r for r in ce if ck(r['chip'])==c]; return (q[0],True) if q else (None,None)
for c,(sc,n) in CPU.items():
    r,isest=pick(c)
    if not r: continue
    if isest: P=r['p']; slp=math.log(r['ehi']/r['elo'])/2
    else: P=r['p']; slp=math.log(r['phi']/r['plo'])/2 if r.get('plo') else 0.1
    dev=r['dev'].replace(' (estimate)','')
    sxx=sx(n)+(0.08 if r['form']=='fanless' else 0)
    how=(f"wall power estimated as 0.9 to 1.1 times the Cinebench all-core wall power of the {r['chip']} {dev} ({P:.0f} W, {'model estimate' if isest else 'Notebookcheck'}). Both are sustained all-core path-tracing loads."
        +(' Fanless Airs throttle in long renders and the median mixes in fan-cooled machines, so this point leans optimistic; the range is widened for it.' if r['form']=='fanless' else ''))
    rows.append(mk('bl-cpu',c,dev,r['form'],sc/60,P,slp,0.095,sxx,f'Blender 4.5 CPU, Open Data median {sc:,.0f} samples/min over {n} run'+('s' if n>1 else ''),
        f"Render speed measured (Blender Open Data median over all {c} machines); "+how,n))
    ns,*v=SCPU[c]
    for scn,spm in zip(SCENES,v):
        rows.append(mk('bl-cpu',c,dev,r['form'],spm/60,P,slp,0.095,sx(ns)+(0.08 if r['form']=='fanless' else 0),f'Blender 4.5 CPU, {scn} scene, Open Data median {spm:,.1f} samples/min over {ns} run'+('s' if ns>1 else ''),
            f"Render speed measured (Blender Open Data median of the {scn} scene over all {c} machines); "+how+' Each scene is assumed to draw the same power as the three-scene run.',ns,scn))
# ---- GPU: power = 0.65 (0.45 to 0.95) x GPU-load (Cyberpunk) wall power
GPUW={'M4':('Mac mini','desktop',39.6,38.2,41),'M4 Pro':('MacBook Pro 14','laptop',80.5,78.7,83),'M4 Max':('MacBook Pro 16','laptop',119.3,115.7,126.9),
      'M5':('MacBook Pro 14','laptop',42.4,41.7,44.2),'M5 Pro':('MacBook Pro 16','laptop',79.8,74.6,81.6),'M5 Max':('MacBook Pro 16','laptop',136.7,133.6,141.8),'M6':('Mac mini','desktop',38.4,37.6,38.9)}
ge={r['chip']:r for r in D['est'] if r['w']=='gpu' and not r.get('mode')}
F=0.65; sF=math.log(0.95/0.45)/2
for c,(gc,sc,n) in GPU.items():
    if c in GPUW:
        dev,form,a,lo,hi=GPUW[c]; G=a; slg=max(math.log(hi/lo)/2,0.03); how=f'measured Cyberpunk 2077 wall power of the {dev} ({a} W, Notebookcheck)'
    elif c in ge:
        g=ge[c]; G=g['p']; slg=math.log(g['ehi']/g['elo'])/2; dev,form=g['dev'].replace(' (estimate)',''),g['form']; how=f"model's estimated GPU-load wall power ({G:.0f} W, itself uncertain by about {100*(math.exp(slg)-1):.0f}%)"
    else: continue
    if '8-core GPU' in dev: gc,sc,n=8,297.36,11
    pw=f'wall power estimated as 0.45 to 0.95 (central 0.65) times the {how}. Cycles on Metal lights the GPU but leaves the CPU nearly idle, whereas the game loads both: Eclectic Light measured about 20 W of GPU power on an M4 Pro Mac mini running the Blender monster scene, against roughly 50 to 60 W of chip power in games. That one reading is the only calibration, hence the wide factor.'
    rows.append(mk('bl-gpu',c,dev,form,sc/60,F*G,slg,sF,sx(n),f'Blender 4.5 Metal, {gc}-core GPU, Open Data median {sc:,.0f} samples/min over {n} run'+('s' if n>1 else ''),
        f'Render speed measured (Blender Open Data median, {gc}-core GPU); '+pw,n))
    ns,*v=SGPU[(c,gc)]
    for scn,spm in zip(SCENES,v):
        rows.append(mk('bl-gpu',c,dev,form,spm/60,F*G,slg,sF,sx(ns),f'Blender 4.5 Metal, {gc}-core GPU, {scn} scene, Open Data median {spm:,.1f} samples/min over {ns} run'+('s' if ns>1 else ''),
            f'Render speed measured (Blender Open Data median of the {scn} scene, {gc}-core GPU); '+pw+' Each scene is assumed to draw the same power as the three-scene run.',ns,scn))
D['est']=[r for r in D['est'] if r['w'] not in ('bl-cpu','bl-gpu')]+rows
D['sources']['blender']=dict(name='Blender Open Data (Blender 4.5.0 medians); power estimated on this page',url='https://opendata.blender.org/benchmarks/query/?blender_version=4.5.0&group_by=device_name')
json.dump(D,open('data4.json','w'),separators=(',',':'))
for w in ('bl-cpu','bl-gpu'):
    print(w)
    for r in sorted([r for r in rows if r['w']==w and not r.get('scene')],key=lambda r:-r['e']): print(f"  {r['chip']:9s} {r['dev']:28s} {r['x']:7.2f}/s P={r['p']:6.1f} [{r['plo']},{r['phi']}] e={r['e']:.3f} [{r['elo']},{r['ehi']}] samples/J")
