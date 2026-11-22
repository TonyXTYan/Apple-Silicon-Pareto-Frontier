"""-> data23.json  M5 Ultra and M3 Ultra Mac Studio rows from ultra_rows.json. No review published wall power for either machine in a
named test, so every row keeps an estimated power (est + pe):
- Cinebench 2024 (M5 Ultra, cpu-all and cpu-one): Notebookcheck's scores replace the model's throughput in the model estimate row,
  as model.py does for the M3 Ultra (KNOWNX): efficiency stays the model estimate with its range (lower end clipped at the score over
  Apple's rated maximum), power is score / efficiency. The row becomes speed measured, power estimated (pe) on the real machine name.
- Geekbench 6 and Cinebench 2026 (CPU Benchmark choice): power borrowed from the same chip's Cinebench 2024 row by the cpubench.py rules
  (Geekbench multi-core 0.8 to 0.95 times the all-core power; single-core and Cinebench 2026 the same power, range widened by 10%).
  For the M3 Ultra that row is the model.py estimate (review speed, model efficiency).
- Blender CPU (M5 Ultra): blender.py borrows the Cinebench all-core power of the chip's estimate row, so the four bl-cpu rows take the
  new row's power and range; speeds are unchanged.
What was searched for and not found is listed in `not_found` of the rows file."""
import json, math
D=json.load(open('data22.json')); J=json.load(open('ultra_rows.json'))
AP={m['chip']:m for m in json.load(open('apple_power.json'))['machines'] if m['dev']=='Mac Studio' and 'Ultra' in m['chip']}
SX=0.02; EXTRA=0.10; GLO,GHI=0.8,0.95; GF=math.sqrt(GLO*GHI); SG=math.log(GHI/GLO)/2     # as cpubench.py
for k,v in J['sources'].items(): D['sources'][k]=dict(v)
def one(L,pred):
    m=[r for r in L if pred(r)]; assert len(m)==1,len(m); return m[0]
# ---- Cinebench 2024: measured speed in place of the model's throughput
cb={}
for c in J['cinebench2024']:
    r=one(D['est'],lambda r:r['w']==c['w'] and r['chip']==c['chip'] and r['src']=='model')
    assert not r['clip']   # the model's lower end is unclipped for the model's own throughput
    x=c['value']; e,ehi,elo=r['e'],r['ehi'],r['elo']; mx=AP[c['chip']]['max_w']; floor=x/mx; clip=elo<floor; elo=max(elo,floor)
    P=x/e; what='multi-core' if c['w']=='cpu-all' else 'single-core'
    note=(f"Score measured by Notebookcheck on a {c['unit']}: {c['test']}, {x:,}. {c['note']} No wall power was published for this machine: efficiency is the "
          f"page's model estimate ({e:.3g} points per joule, {elo:.3g} to {ehi:.3g}), as for the M3 Ultra, whose Cinebench speed also comes from reviews, and power is the score divided by it "
          f"({P:.0f} W, {x/ehi:.0f} to {x/elo:.0f} W). The range is the model's leave-one-out spread, widened 1.5 times because no M5 Ultra has a wall reading"
          +(f", with the lower end of efficiency clipped at the score divided by Apple's rated maximum of {mx:g} W" if clip else '')+
          f". It replaces the model's own throughput estimate ({r['x']:,.0f}).")
    r.update(dev='Mac Studio',x=x,xlo=round(x*math.exp(-SX),1),xhi=round(x*math.exp(SX),1),elo=round(elo,4),p=round(P,1),plo=round(x/ehi,1),phi=round(x/elo,1),
             q='E',est=1,pe=1,seen=True,clip=clip,src=c['src'],bench=f"Cinebench 2024 {what} (Notebookcheck, Mac17,15)",note=note)
    cb[(c['w'],c['chip'])]=r
# ---- Geekbench 6 and Cinebench 2026, power borrowed from the Cinebench 2024 row (cpubench.py rules)
def base(w,chip):
    if (w,chip) in cb: return cb[(w,chip)]
    r=one(D['est'],lambda r:r['w']==w and r['chip']==chip and r['src']=='model')
    return dict(r,plo=round(r['x']/r['ehi'],1),phi=round(r['x']/r['elo'],1))
def src(k,bm):
    k2=('gb_' if bm.startswith('Geekbench') else 'cb26_')+k
    D['sources'].setdefault(k2,dict(name=J['sources'][k]['name']+' ('+bm+' scores; power estimated on this page)',url=J['sources'][k]['url'])); return k2
rows=[]
for c in J['cpubench']:
    w,chip,bm=c['w'],c['chip'],c['bm']; b=base(w,chip); hw=math.log(b['phi']/b['plo'])/2
    runs=c['runs']; x=sum(runs)/len(runs)
    bp=(f"this machine's Cinebench 2024 {'all-core' if w=='cpu-all' else 'single-thread'} power ({b['p']:g} W, {b['plo']:g} to {b['phi']:g} W), "
        +("itself Notebookcheck's score divided by the model's efficiency, since no wall power was published" if b['src']!='model' else "itself the review score divided by the model's efficiency (model estimate)"))
    if w=='cpu-all' and bm=='Geekbench 6':
        P=GF*b['p']; sP=math.sqrt(hw*hw+SG*SG)
        pw=f"0.8 to 0.95 times (central {GF:.2f}) {bp}: Geekbench 6 multi-core is short and bursty and does not keep every core busy the whole time, so it should draw a little less than a sustained render"
    else:
        P=b['p']; sP=math.sqrt(hw*hw+EXTRA*EXTRA)
        pw=bp+", with the range widened by 10%"+(", since one busy thread draws about the same in either benchmark" if w=='cpu-one' else ", since both are sustained all-core renders")
    s=math.sqrt(sP*sP+SX*SX); e=x/P
    who='Notebookcheck' if c['src']=='nbc_m5u' else 'Gearlive'
    sc=', '.join(f'{v:,}' for v in runs)+(f' (mean {x:,.1f})' if len(runs)>1 else '')
    ver=(f"Geekbench {c['version']}" if c['version'] and bm=='Geekbench 6' else bm)
    note=(f"Score measured by {who} ({c['unit']}; {c['test']}, {sc}). {c['note']} No wall power was published for {bm.replace('Geekbench 6','Geekbench')}: power is estimated as {pw}.")
    th='multi' if w=='cpu-all' else 'single'
    r=dict(w=w,bm=bm,chip=chip,dev='Mac Studio',tier='Ultra',form='desktop',x=round(x,1),xlo=round(x*math.exp(-SX),1),xhi=round(x*math.exp(SX),1),e=round(e,3),elo=round(e*math.exp(-s),3),ehi=round(e*math.exp(s),3),
           p=round(P,1),plo=round(P*math.exp(-sP),1),phi=round(P*math.exp(sP),1),q='E',est=1,pe=1,seen=True,src=src(c['src'],bm),resc=False,bench=f"{ver} {th}-core",note=note)
    rows.append(r)
D['est']+=rows
# ---- Blender CPU (M5 Ultra): power follows the new Cinebench 2024 all-core row (blender.py: 0.9 to 1.1 times it)
cr=cb[('cpu-all','M5 Ultra')]; slp=math.log(cr['ehi']/cr['elo'])/2; sF=0.095
bl=[r for r in D['est'] if r['w']=='bl-cpu' and r['chip']=='M5 Ultra']; assert len(bl)==4
for r in bl:
    old=r['p']; sxx=math.log(r['xhi']/r['xlo'])/2; P=cr['p']; e=r['x']/P; s=math.sqrt(sxx**2+slp**2+sF**2); sp=math.sqrt(slp**2+sF**2)
    oldtxt=f"M5 Ultra Mac Studio ({old:.0f} W, model estimate)"; assert oldtxt in r['note'],r['note']
    r.update(e=round(e,4),elo=round(e*math.exp(-s),4),ehi=round(e*math.exp(s),4),p=round(P,1),plo=round(P*math.exp(-sp),1),phi=round(P*math.exp(sp),1),
             note=r['note'].replace(oldtxt,f"M5 Ultra Mac Studio ({P:.0f} W: Notebookcheck's Cinebench 2024 score divided by the model's efficiency, since no wall power was published)"))
json.dump(D,open('data23.json','w'),separators=(',',':'))
for r in list(cb.values())+rows+bl:
    print(f"{r['w']:7} {r.get('bm') or r.get('scene') or '':14} {r['chip']:9} {r['dev']:22} x={r['x']:<9} P={r['p']:6} [{r.get('plo')},{r.get('phi')}] e={r['e']} [{r['elo']},{r['ehi']}]")
