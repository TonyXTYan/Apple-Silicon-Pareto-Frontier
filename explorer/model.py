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
# Apple official wall power (idle, max) by chip and machine
APPLE={('M5 Max','Mac Studio'):(7,200),('M5 Ultra','Mac Studio'):(9,385),('M4 Max','Mac Studio'):(6,145),('M3 Ultra','Mac Studio'):(9,270),
 ('M2 Max','Mac Studio'):(9,145),('M2 Ultra','Mac Studio'):(10,295),('M1 Max','Mac Studio'):(11,115),('M1 Ultra','Mac Studio'):(13,215),
 ('M4','Mac mini'):(4,65),('M4 Pro','Mac mini'):(5,140),('M2','Mac mini'):(7,50),('M2 Pro','Mac mini'):(7,100),('M1','Mac mini'):(7,39)}
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
D['apple']=[dict(chip=c,dev=d,idle=a,max=b) for (c,d),(a,b) in APPLE.items()]
D['sources'].update({
 'model':dict(name='Estimate from the fitted model on this page',url='#method'),
 'modes':dict(name='Digital Trends scores; Notebookcheck and Eclectic Light package power',url='https://digitaltrends.com/computing/m4-pro-low-power-mode-change'),
 'apple_studio':dict(name='Apple, Mac Studio power consumption',url='https://support.apple.com/102027'),
 'apple_mini':dict(name='Apple, Mac mini power consumption',url='https://support.apple.com/103253')})
for r in R: r.pop('ck',None)
json.dump(D,open('data2.json','w'),separators=(',',':'))
for e in est:
    if e['w'] in('cpu-all','hpl') : print(f"{e['w']:8s} {e['chip']:10s} x={e['x']:8.1f} e={e['e']:.3f} [{e['elo']:.3f},{e['ehi']:.3f}] sd={e['sd']} seen={e['seen']} clip={e['clip']}")
