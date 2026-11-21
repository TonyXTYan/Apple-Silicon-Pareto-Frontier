"""-> data12.json  CPU benchmark menu: Geekbench 6 and Cinebench 2026 scores (Notebookcheck, cpubench_rows.json) for the review
units whose Cinebench wall power is on this page. No wall power was published for these runs, so power is borrowed from the
same machine's Cinebench rows: single-core = Cinebench single-thread wall power (range widened by 10%), Geekbench multi-core =
0.8 to 0.95 times the Cinebench all-core wall power, Cinebench 2026 = the Cinebench 2024 wall power (widened by 10%).
Machines with only Geekbench 5.5 are converted to Geekbench 6.7 with a ratio fitted on the machines that have both, as the
page converts Cinebench R23 to 2024; the conversion error goes into the error bars and those points are drawn hollow."""
import json, math
D=json.load(open('data11.json')); X=json.load(open('cpubench_rows.json'))['sets']
CB={(r['w'],r['chip'],r['dev']):r for r in D['rows'] if r['w'] in ('cpu-all','cpu-one') and r['chip'][0]=='M'}
def S(prefix,threads):
    s=[s for s in X if s['name'].startswith(prefix) and s['threads']==threads]; assert len(s)==1; return s[0]
SX=0.02          # one run on one unit: about 1 to 2% run-to-run noise
EXTRA=0.10       # extra log spread for borrowing power from another benchmark
GLO,GHI=0.8,0.95; GF=math.sqrt(GLO*GHI); SG=math.log(GHI/GLO)/2   # Geekbench multi-core power as a fraction of Cinebench all-core
url2key={}
for k,v in D['sources'].items():
    if v['url'] not in url2key or k.startswith('nbc_'): url2key[v['url']]=k   # prefer the page's own Notebookcheck source names
def src(u,bm):
    k=('gb_' if bm.startswith('Geekbench') else 'cb26_')+url2key[u]
    if k not in D['sources']: D['sources'][k]=dict(name=D['sources'][url2key[u]]['name']+' ('+bm+' scores; power estimated on this page)',url=u)
    return k
rows=[]; stitch={}
def add(w,chip,dev,bm,x,u,sx,bench,how,resc=False,raw=None,extra=''):
    b=CB[(w,chip,dev)]; hw=math.log(b['phi']/b['plo'])/2
    if w=='cpu-all' and bm=='Geekbench 6': P=GF*b['p']; sP=math.sqrt(hw*hw+SG*SG); pw=f"0.8 to 0.95 times (central {GF:.2f}) this machine's Cinebench {'R23' if b['resc'] else '2024'} all-core wall power ({b['p']:g} W, {b['plo']:g} to {b['phi']:g} W): Geekbench 6 multi-core is short and bursty and does not keep every core busy the whole time, so it should draw a little less than a sustained render"
    else:
        P=b['p']; sP=math.sqrt(hw*hw+EXTRA*EXTRA)
        pw=f"this machine's Cinebench {'R23' if b['resc'] else '2024'} {'single-thread' if w=='cpu-one' else 'all-core'} wall power ({b['p']:g} W, {b['plo']:g} to {b['phi']:g} W), with the range widened by 10%"+(", since one busy thread draws about the same in either benchmark" if w=='cpu-one' else ", since both are sustained all-core renders")
    s=math.sqrt(sP*sP+sx*sx); e=x/P
    note=f"Score measured by Notebookcheck on this review unit ({how}). No wall power was published for {bm.replace('Geekbench 6','Geekbench')}: power is estimated as {pw}."+(' '+extra if extra else '')
    r=dict(w=w,bm=bm,chip=chip,dev=dev,tier=b['tier'],form=b['form'],x=round(x,1),xlo=round(x*math.exp(-sx),1),xhi=round(x*math.exp(sx),1),e=round(e,3),elo=round(e*math.exp(-s),3),ehi=round(e*math.exp(s),3),
           p=round(P,1),plo=round(P*math.exp(-sP),1),phi=round(P*math.exp(sP),1),q='E',est=1,pe=1,seen=True,src=src(u,bm),resc=resc,bench=bench,note=note)
    if raw is not None: r['raw']=raw
    rows.append(r)
M3NOTE='Notebookcheck\'s M3 analysis text says Geekbench 6.2, its table says 6.7; 6.7 is used.'
PAIR='Notebookcheck lists two M4 Pro 12-core MacBook Pro 14 units (3,844 / 20,458 and 3,837 / 20,385); the first is paired with the Cinebench 2024 row (1,435) by listing order.'
for w,th in (('cpu-all','multi'),('cpu-one','single')):
    g6={(r['chip'],r['device']):r for r in S('Geekbench 6.7',th)['rows']}; g5={(r['chip'],r['device']):r for r in S('Geekbench 5.5',th)['rows']}
    both=[k for k in g6 if k in g5]; lr=[math.log(g6[k]['value']/g5[k]['value']) for k in both]; m=sum(lr)/len(lr)
    sig=math.sqrt(sum((v-m)**2 for v in lr)/(len(lr)-1)); k6=math.exp(m); stitch[w]=dict(k=k6,sig=sig,n=len(both),res=[(k,round(math.exp(v-m),3)) for k,v in zip(both,lr)])
    for (c,d),r in g6.items():
        extra=' '.join(t for t in ((M3NOTE if 'Apple-M3-SoC' in r['source_url'] else ''),(PAIR if (c,d)==('M4 Pro 12c','MacBook Pro 14') else '')) if t)
        add(w,c,d,'Geekbench 6',r['value'],r['source_url'],SX,f'Geekbench 6.7 {th}-core',f"Geekbench 6.7 {th}-core, {r['value']:,}",extra=extra)
    for (c,d),r in g5.items():
        if (c,d) in g6: continue
        x=r['value']*k6; sx=math.sqrt(SX*SX+sig*sig)
        add(w,c,d,'Geekbench 6',x,r['source_url'],sx,f"Geekbench 5.5 {th}-core ({r['value']:,}), converted to Geekbench 6.7",
            f"Geekbench 5.5 {th}-core, {r['value']:,}",resc=True,raw=r['value'],
            extra=f"Converted to Geekbench 6.7 with the ratio of the {len(both)} machines Notebookcheck ran in both ({k6:.3f}); they scatter by {sig*100:.0f}% around it, which is added to the error bars."
              +(" Larger chips gain less from 5.5 to 6.7 in multi-core (Max chips about 0.92 to 0.96, base chips about 1.1), so this conversion may flatter a Max or Pro chip and understate a base chip." if w=='cpu-all' else ''))
    for r in S('Cinebench 2026',th)['rows']:
        add(w,r['chip'],r['device'],'Cinebench 2026',r['value'],r['source_url'],SX,f'Cinebench 2026 {th}-core',f"Cinebench 2026 {th}-core, {r['value']:,}")
D['est']+=rows; D['stitch_gb']={('all' if w=='cpu-all' else 'one'):dict(k=round(v['k'],4),sig=round(v['sig']*100,1),n=v['n']) for w,v in stitch.items()}
json.dump(D,open('data12.json','w'),separators=(',',':'))
for w,v in stitch.items(): print(w,'GB5.5->6.7 ratio %.3f rms %.3f n=%d'%(v['k'],v['sig'],v['n']),v['res'])
for r in rows: print(f"{r['w']:7} {r['bm']:14} {r['chip']:10} {r['dev']:28} x={r['x']:8} P={r['p']:6} [{r['plo']},{r['phi']}] e={r['e']} [{r['elo']},{r['ehi']}] {'resc' if r['resc'] else ''}")
