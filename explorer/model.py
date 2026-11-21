import json, numpy as np, re, collections
D=json.load(open('data.json')); R=D['rows']
def ckey(c): return re.sub(r' \d+c$','',c)
def gen(c):
    m=re.match(r'M(\d)',c); return int(m.group(1)) if m else None
for r in R: r['ck']=ckey(r['chip']); r['gen']=gen(r['chip'])
WS=['cpu-all','cpu-one','hpl','gpu']; TIERS=['base','Pro','Max','Ultra']
# chip-level observations: mean log over machines (excluding flagged-overstated and weak-method rows)
obs=collections.defaultdict(list)
for r in R:
    if r['w'] in WS and r['gen'] and not r.get('ex') and r['q']!='C':
        obs[(r['ck'],r['w'])].append((np.log(r['e']),np.log(r['x'])))
cells={k:(np.mean([a for a,b in v]),np.mean([b for a,b in v]),len(v)) for k,v in obs.items()}
tier_of={r['ck']:r['tier'] for r in R if r['gen']}
chips=sorted({k[0] for k in cells}|{'M1 Ultra','M2 Ultra','M3 Ultra','M5 Ultra'},key=lambda c:(gen(c),TIERS.index(tier_of.get(c,'Ultra'))))
for c in ['M1 Ultra','M2 Ultra','M5 Ultra']: tier_of[c]='Ultra'
tier_of['M3 Ultra']='Ultra'
gens=sorted({gen(c) for c in chips})
# parameters: b_w (free), d_{w,t} (ridge .15), g_gen (ridge 1), t_tier (ridge 1), u_c (ridge .2)
P=[]; idx={}
def add(name,prior): idx[name]=len(P); P.append(prior)
for w in WS: add(('b',w),None)
for w in WS:
    for t in TIERS: add(('d',w,t),.15)
for g in gens: add(('g',g),1.0)
for t in TIERS: add(('t',t),1.0)
for c in chips: add(('u',c),.2)
def design(c,w):
    v=np.zeros(len(P)); t=tier_of[c]
    for k in [('b',w),('d',w,t),('g',gen(c)),('t',t),('u',c)]: v[idx[k]]=1
    return v
XONLY={('M3 Ultra','cpu-all'):np.log(3062),('M3 Ultra','cpu-one'):np.log(145),('M2 Ultra','cpu-all'):np.log(28550/14.45)}
def val(k,col): return cells[k][col] if k in cells else XONLY[k]
def fit(keys,col,sig=.08):
    A=np.array([design(c,w) for c,w in keys]); y=np.array([val(k,col) for k in keys])
    L=np.diag([0 if p is None else 1/p**2 for p in P]); W=1/sig**2
    M=W*A.T@A+L; th=np.linalg.solve(M,W*A.T@y); return th,np.linalg.inv(M)
keys=sorted(cells)
out={}
for col,nm in ((0,'e'),(1,'x')):
    fk=keys if col==0 else sorted(set(keys)|set(XONLY))
    th,cov=fit(fk,col)
    res=collections.defaultdict(list); loo=[]
    for k in keys:
        if sum(1 for kk in keys if kk[0]==k[0])<2: continue   # need the chip seen elsewhere to test interpolation
        k2=[kk for kk in fk if kk!=k]; th2,_=fit(k2,col)
        p=design(*k)@th2; res[k[1]].append(cells[k][col]-p); loo.append(dict(chip=k[0],w=k[1],meas=float(np.exp(cells[k][col])),pred=float(np.exp(p))))
    sig={w:float(np.sqrt(np.mean(np.square(v)))) if v else None for w,v in res.items()}
    out[nm]=dict(th=th,cov=cov,sig=sig,loo=loo,n={w:len(v) for w,v in res.items()})
    print(nm,'LOO rms (log) by workload:',{w:round(s,3) for w,s in sig.items()},'n=',out[nm]['n'])
# Apple's published power figures (apple_power.json). Desktops: support-page idle and maximum wall power, whose maximum is
# a floor on work per joule below; sleep and off from the environmental report. Laptops: environmental-report idle with the
# display on, sleep and off (115 V), adapter and battery. A laptop's adapter is not a cap (the battery can add to it), so
# laptops are shown only, never used as a bound.
AP=json.load(open('apple_power.json'))['machines']
APPLE={(ckey(m['chip']),m['dev']):(m['idle_w'],m['max_w']) for m in AP if m['kind']=='desktop'}
# published throughputs without wall power, used in place of the model's throughput
KNOWNX={('M3 Ultra','cpu-all'):(3062,3028,3082,'Cinebench 2024 multi-core 3,028 to 3,082 across XDA, Ars Technica and PC Watch reviews'),
        ('M3 Ultra','cpu-one'):(145,141,150,'Cinebench 2024 single-core 141 to 150 across reviews'),
        ('M2 Ultra','cpu-all'):(1976,1878,2074,'Cinebench R23 multi-core 28,550 (TechRadar), converted to Cinebench 2024 units with a 5% conversion uncertainty')}
est=[]
SAMPLE_FORM={}
for r in R:
    if r['gen'] and r['w'] in WS: SAMPLE_FORM.setdefault(r['ck'],collections.Counter())[(r['form'],r['dev'])]+=1
for c in chips:
    for w in WS:
        if (c,w) in cells: continue
        v=design(c,w); seen=any(k[0]==c for k in keys)
        le=v@out['e']['th']; lx=v@out['x']['th']
        se=np.sqrt(out['e']['sig'][w]**2+float(v@out['e']['cov']@v)); sx=np.sqrt(out['x']['sig'][w]**2+float(v@out['x']['cov']@v))
        if not seen: se*=1.5; sx*=1.5
        form,dev=('desktop','Mac Studio') if tier_of[c]=='Ultra' else SAMPLE_FORM.get(c,collections.Counter({('laptop','MacBook Pro'):1})).most_common(1)[0][0]
        x=float(np.exp(lx)); xlo=float(np.exp(lx-sx)); xhi=float(np.exp(lx+sx)); note=''
        if (c,w) in KNOWNX: x,xlo,xhi,note=KNOWNX[(c,w)]; note+='. Efficiency is the model estimate.'
        e=float(np.exp(le)); elo=float(np.exp(le-se)); ehi=float(np.exp(le+se))
        ap=APPLE.get((c,dev)); clip=False
        if ap and w!='gpu':
            floor=x/ap[1]
            if elo<floor: elo=floor; clip=True
        est.append(dict(w=w,chip=c,ck=c,gen=gen(c),dev=dev+' (estimate)',tier=tier_of[c],form=form,x=round(x,2),xlo=round(xlo,2),xhi=round(xhi,2),
            e=round(e,4),elo=round(elo,4),ehi=round(ehi,4),p=round(x/e,1),q='E',est=1,bench='Model estimate',src='model',resc=False,
            sd=round(float(se),3),seen=seen,clip=clip,note=note))
print(len(est),'estimates')
# Power modes, Mac mini M4 Pro 14-core: published scores per mode, wall power estimated from published SoC power
MODES=[('Low Power',765,(11,13.5)),('Automatic',1622,(38,42)),('High Power',1707,(44,48))]
modes=[]
for m,x,(lo,hi) in MODES:
    wlo,whi=1.15*lo+6,1.15*hi+10; wm=(wlo+whi)/2
    modes.append(dict(w='cpu-all',chip='M4 Pro 14c',ck='M4 Pro',gen=4,dev='Mac mini, '+m,mode=m,tier='Pro',form='desktop',x=x,e=round(x/wm,3),elo=round(x/whi,3),ehi=round(x/wlo,3),
        p=round(wm,1),plo=round(wlo,1),phi=round(whi,1),q='E',est=1,bench='Cinebench 2024 multi-core, '+m+' mode',src='modes',resc=False,
        note='Score measured by Digital Trends. Wall power is estimated: CPU package power from Notebookcheck (High, Automatic) and Eclectic Light (Low Power cap of 13.5 W), scaled by 1.15 for conversion losses plus 6 to 10 W for the rest of the machine.'))
for r in modes: print(r['dev'],r['e'],r['elo'],r['ehi'],r['p'])
D['est']=est+modes
D['loo']={k:out[k]['loo'] for k in ('e','x')}; D['loosig']={k:out[k]['sig'] for k in ('e','x')}
def apple_entries():
    out=[]; S2=D['sources']
    def per(u):
        stem=u.rsplit('/',1)[1].replace('.pdf',''); k='per_'+stem
        t,dt=stem.split('_PER_'); S2.setdefault(k,dict(name='Apple, '+t.replace('_',' ')+' Product Environmental Report ('+re.sub(r'([A-Za-z])(\d)',r'\1 \2',dt)+')',url=u)); return k
    def specs(u):
        k='specs_'+u.rsplit('/',1)[1]; S2.setdefault(k,dict(name='Apple, technical specifications (support article '+u.rsplit('/',1)[1]+')',url=u)); return k
    for m in AP:
        n=m.get('notes',''); notes=[]
        if m['kind']=='desktop':
            e=dict(chip=ckey(m['chip']),dev=m['dev'],kind='desktop',idle=m['idle_w'],max=m['max_w'],src='apple_mini' if m['dev']=='Mac mini' else 'apple_studio')
            if m.get('max_definition')=='CPU Max': e['cpumax']=1; notes.append('Apple\'s maximum for this Mac mini is "CPU Max", a CPU-only load, so a combined CPU and GPU load can exceed it.')
            if m.get('sleep_w') is not None: e.update(sleep=m['sleep_w'],off=m['off_w'])
            if m.get('url_per'): e['per']=per(m['url_per'])
            if m['chip'].endswith('c') and 'Pro' in m['chip']: notes.append('Apple gives one M4 Pro Mac mini figure (64 GB, 8 TB) without a core count, and none per power mode.')
            if 'identical to the Jan 2023 M2 table' in n: notes.append('The M4 Mac mini environmental report repeats the M2 Mac mini table exactly, so its sleep and off figures are not an independent measurement.')
        elif 'energy_star' in m:
            es=m['energy_star']; e=dict(chip=m['chip'],dev=m['dev'],kind='laptop',es=dict(short=es['short_idle_w'],long=es['long_idle_w'],sleep=es['sleep_w'],off=es['off_w']),adapter=m['adapter_w'],battery=m['battery_wh'],
                src='energystar_a3185',specs=specs(m['url_specs'])); S2['energystar_a3185']=dict(name='ENERGY STAR certification, MacBook Pro 14-inch (M4 Max), A3185',url=m['url_power']); notes.append(m['notes'])
        else:
            e=dict(chip=m['chip'],dev=m['dev'],kind='laptop',idle_on=m['idle_display_on_w'],sleep=m['sleep_w'],off=m['off_w'],adapter=m['adapter_w'],battery=m['battery_wh'],src=per(m['url_power']),specs=specs(m['url_specs']))
            if m.get('match','').startswith('proxy'): e['proxy']='M3 Pro table'; notes.append('The October 2023 report has idle tables only for the 14-inch M3 and M3 Pro, so the M3 Pro table stands in for the M3 Max.')
            if 'identical to the 2023' in n: notes.append('Apple\'s '+m['chip'].split(' 1')[0]+' table repeats its 2023 '+m['chip'].split(' 1')[0].replace('M4','M3')+' table exactly, so it is not an independent measurement.')
            cov=re.search(r'covering ([^;]+?);',n)
            if cov: notes.append('One table covers '+cov.group(1)+'.')
            v=m.get('v230')
            if v: notes.append(f"At 230 V Apple lists idle {v['idle_display_on']:g} W, sleep {v['sleep']:g} W and off {v['off']:g} W.")
        if notes: e['note']=' '.join(notes)
        out.append(e)
    return out
D['apple']=apple_entries()
D['sources'].update({
 'model':dict(name='Estimate from the fitted model on this page',url='#method'),
 'modes':dict(name='Digital Trends scores; Notebookcheck and Eclectic Light package power',url='https://digitaltrends.com/computing/m4-pro-low-power-mode-change'),
 'apple_studio':dict(name='Apple, Mac Studio power consumption',url='https://support.apple.com/102027'),
 'apple_mini':dict(name='Apple, Mac mini power consumption',url='https://support.apple.com/103253')})
for r in R: r.pop('ck',None)
json.dump(D,open('data2.json','w'),separators=(',',':'))
for e in est:
    if e['w'] in('cpu-all','hpl') : print(f"{e['w']:8s} {e['chip']:10s} x={e['x']:8.1f} e={e['e']:.3f} [{e['elo']:.3f},{e['ehi']:.3f}] sd={e['sd']} seen={e['seen']} clip={e['clip']}")
