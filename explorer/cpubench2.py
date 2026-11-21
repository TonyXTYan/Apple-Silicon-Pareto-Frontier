"""-> data18.json  CPU benchmark menu for the comparison machines: Notebookcheck Geekbench 6.7 single/multi-core and Cinebench 2026
scores (cpubench2_rows.json) for the Intel, AMD, Qualcomm and NVIDIA review units whose Cinebench wall power is on this page.
Power is borrowed from that machine's Cinebench rows exactly as cpubench.py does for the Macs: single-core = Cinebench
single-thread wall power (range widened by 10%), Geekbench multi-core = 0.8 to 0.95 times the Cinebench all-core wall power,
Cinebench 2026 = the Cinebench 2024 wall power (widened by 10%). Every unit here has a Geekbench 6.7 run, so no Geekbench 5.5
conversion is needed (the 5.5 scores stay in the rows file for reference). Machines whose Cinebench run boosts well above its
sustained level (PL2 > PL1) get a caveat: Geekbench's short bursts may sit nearer the boost power than the 0.8-0.95 factor
assumes, and no Geekbench power reading exists to check it, so the factor is kept and the note says so."""
import json, math
D=json.load(open('data17.json')); X=json.load(open('cpubench2_rows.json'))['rows']
CB={(r['w'],r['chip'],r['dev']):r for r in D['rows'] if r['w'] in ('cpu-all','cpu-one') and r['chip'][0]!='M' and not r.get('bm') and not r.get('srv')}
SX=0.02          # one run on one unit: about 1 to 2% run-to-run noise
EXTRA=0.10       # extra log spread for borrowing power from another benchmark
GLO,GHI=0.8,0.95; GF=math.sqrt(GLO*GHI); SG=math.log(GHI/GLO)/2
BOOST=1.3        # Cinebench max wall power over its average above which the burst caveat is added
url2key={}
for k,v in D['sources'].items():
    if v['url'] not in url2key or k.startswith('nbc_'): url2key[v['url']]=k
def src(u,bm,unit):
    pre='gb_' if bm.startswith('Geekbench') else 'cb26_'
    if u in url2key: k=pre+url2key[u]; name=D['sources'][url2key[u]]['name']
    else: k=pre+'x_'+unit.lower().replace(' ','_').replace('(','').replace(')',''); name='Notebookcheck, '+unit+' review'
    if k not in D['sources']: D['sources'][k]=dict(name=name+' ('+bm+' scores; power estimated on this page)',url=u)
    return k
rows=[]
def add(w,m,bm,vals,bench):
    b=CB[(w,m['chip'],m['device'])]; hw=math.log(b['phi']/b['plo'])/2
    x=math.exp(sum(math.log(v) for v in vals)/len(vals)); spread=math.log(max(vals)/min(vals))/2; sx=math.sqrt(SX*SX+spread*spread)
    how=bench+', '+' and '.join(f'{v:,}' for v in vals)+(f' (two runs of this unit, geometric mean {x:,.0f}; their spread is added to the error bars)' if len(vals)>1 else '')
    if w=='cpu-all' and bm=='Geekbench 6':
        P=GF*b['p']; sP=math.sqrt(hw*hw+SG*SG)
        pw=f"0.8 to 0.95 times (central {GF:.2f}) this machine's Cinebench 2024 all-core wall power ({b['p']:g} W, {b['plo']:g} to {b['phi']:g} W): Geekbench 6 multi-core is short and bursty and does not keep every core busy the whole time, so it should draw a little less than a sustained render"
        if b['phi']/b['p']>BOOST: pw+=(f". Caveat: this machine's Cinebench run peaks at {b['phi']:g} W against a {b['p']:g} W average (a high short-term power limit), and Geekbench's short bursts may sit nearer that peak, "
            "so its real Geekbench power could be higher and its points per joule lower than shown; the review gives no Geekbench power reading to check, so the 0.8 to 0.95 factor is kept")
    else:
        P=b['p']; sP=math.sqrt(hw*hw+EXTRA*EXTRA)
        pw=f"this machine's Cinebench 2024 {'single-thread' if w=='cpu-one' else 'all-core'} wall power ({b['p']:g} W, {b['plo']:g} to {b['phi']:g} W), with the range widened by 10%"+(", since one busy thread draws about the same in either benchmark" if w=='cpu-one' else ", since both are sustained all-core renders")
    s=math.sqrt(sP*sP+sx*sx); e=x/P
    note=f"Score measured by Notebookcheck on this review unit ({how}). No wall power was published for {bm.replace('Geekbench 6','Geekbench')}: power is estimated as {pw}. {m['notes']}"
    rows.append(dict(w=w,bm=bm,chip=m['chip'],dev=m['device'],tier=b['tier'],form=b['form'],x=round(x,1),xlo=round(x*math.exp(-sx),1),xhi=round(x*math.exp(sx),1),e=round(e,3),elo=round(e*math.exp(-s),3),ehi=round(e*math.exp(s),3),
        p=round(P,1),plo=round(P*math.exp(-sP),1),phi=round(P*math.exp(sP),1),q='E',est=1,pe=1,seen=True,src=src(m['source_url'],bm,m['nbc_unit']),resc=False,bench=bench,note=note,sl=b['sl'],sd=b['sd']))
for m in X:
    assert m['gb67_multi'] and m['gb67_single'], m['device']
    for w,th in (('cpu-all','multi'),('cpu-one','single')):
        if (w,m['chip'],m['device']) not in CB: continue   # no wall power on this tab (Framework Desktop single-core)
        add(w,m,'Geekbench 6',m['gb67_'+th],f'Geekbench 6.7 {th}-core')
        if m['cb26_'+th]: add(w,m,'Cinebench 2026',[m['cb26_'+th]],f'Cinebench 2026 {th}-core')
D['est']+=rows
json.dump(D,open('data18.json','w'),separators=(',',':'))
for r in rows: print(f"{r['w']:7} {r['bm']:14} {r['chip'][:24]:24} {r['dev'][:34]:34} x={r['x']:8} P={r['p']:6} [{r['plo']},{r['phi']}] e={r['e']} [{r['elo']},{r['ehi']}]")
