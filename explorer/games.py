"""-> data8.json  Baldur's Gate 3 and Assassin's Creed Shadows frame rates (Notebookcheck) on the machines that already
have a metered Cyberpunk 2077 row. Speed is measured; wall power is that machine's Cyberpunk reading, widened by 12%,
because nobody published wall power in these games. Total War: Pharaoh (engine-capped near 50-56 fps) and Shadow of the
Tomb Raider (no M5-family results) are left out; see the README."""
import json, math
D=json.load(open('data7.json'))
CP='Cyberpunk 2077'
for r in D['rows']+D['est']:
    if r['w']=='gpu': r['game']=CP
cp={(r['chip'],r['dev']):r for r in D['rows'] if r['w']=='gpu'}
N='https://www.notebookcheck.net/'
U={'m5air':N+'Apple-M5-8-Core-GPU-Benchmarks-and-Specs.1244908.0.html',
   'm5pm':N+'Apple-M5-Pro-M5-Max-GPU-Analysis-M5-Max-GPU-on-par-with-the-GeForce-RTX-5070-and-faster-than-Strix-Halo.1246060.0.html',
   'm4max':N+'Apple-M4-Max-40-core-GPU-Benchmarks-and-Specs.920457.0.html',
   'm4pro':N+'Apple-M4-Pro-20-core-GPU-Benchmarks-and-Specs.915517.0.html',
   'mini4':N+'Apple-Mac-Mini-M4-review-Smaller-faster-and-louder.918832.0.html',
   'm6':N+'Apple-M6-12-Core-GPU-Benchmarks-and-Specs.1401995.0.html',
   'm4acs':N+'Cyberpunk-AC-Shadows-on-Apple-s-M4-Max-Gaming-performance-comparable-to-the-RTX-5060-Laptop.1166765.0.html'}
UN={'m5air':'Notebookcheck, M5 8-core GPU (MacBook Air 13 M5)','m5pm':'Notebookcheck, M5 Pro and M5 Max GPU analysis',
    'm4max':'Notebookcheck, M4 Max 40-core GPU','m4pro':'Notebookcheck, M4 Pro 20-core GPU','mini4':'Notebookcheck, Mac mini M4 review',
    'm6':'Notebookcheck, M6 12-core GPU (Mac mini M6)','m4acs':'Notebookcheck, Cyberpunk 2077 and AC Shadows on the M4 Max (native vs CrossOver)'}
GAMES={'bg3':("Baldur's Gate 3","Baldur's Gate 3, 1080p Ultra, AA:T"),'acs':("Assassin's Creed Shadows","Assassin's Creed Shadows, 1080p Ultra High")}
# (game, chip, dev, fps, source, extra note)
FPS=[('bg3','M5','MacBook Air 13',28.5,'m5air','In Baldur\'s Gate 3 Notebookcheck measured 7.5 to 7.8 W at the chip against 6.9 to 7.2 W in Cyberpunk, so wall power here is probably a little above the Cyberpunk reading. The Air is fanless and throttles under a long load.'),
     ('bg3','M5','MacBook Pro 14',47.0,'m5pm',''),
     ('bg3','M5 Pro','MacBook Pro 16',83.8,'m5pm',''),
     ('bg3','M5 Max','MacBook Pro 16',134.6,'m5pm',''),
     ('bg3','M5 Max','MacBook Pro 14',122.1,'m5pm',''),
     ('bg3','M4 Max','MacBook Pro 16',99,'m4max',''),
     ('bg3','M4 Pro 14c','MacBook Pro 14',61,'m4pro',''),
     ('bg3','M4','Mac mini',30.1,'mini4','The only native game in that review; its Cyberpunk run, whose power is borrowed here, was a translated build.'),
     ('bg3','M6','Mac mini',58.1,'m6',''),
     ('acs','M5','MacBook Air 13',11,'m5air','Notebookcheck rates this unplayable. The Air is fanless and throttles under a long load.'),
     ('acs','M5','MacBook Pro 14',16,'m5pm',''),
     ('acs','M5 Pro','MacBook Pro 16',26,'m5pm',''),
     ('acs','M5 Max','MacBook Pro 16',42,'m5pm',''),
     ('acs','M5 Max','MacBook Pro 14',41,'m5pm',''),
     ('acs','M4 Max','MacBook Pro 16',33,'m4acs','Native build; the article text says about 30 fps.'),
     ('acs','M6','Mac mini',23,'m6','')]
EXTRA=0.12   # extra log spread on power for borrowing it from another game (about +-12%)
SX=0.03      # frame-rate spread (one review run per point)
rows=[]
for g,chip,dev,fps,sk,extra in FPS:
    b=cp[(chip,dev)]; game,bench=GAMES[g]
    P=b['p']; sP=math.sqrt((math.log(b['phi']/b['plo'])/2)**2+EXTRA**2); s=math.sqrt(sP*sP+SX*SX); e=fps/P
    note=(f'Frame rate measured by Notebookcheck. Wall power is this machine\'s Cyberpunk 2077 reading ({P:g} W, {b["plo"]:g} to {b["phi"]:g} W), '
          f'because no wall power was published for {game}; it was measured in Cyberpunk, not this game, so the range is widened by about {EXTRA*100:.0f}%.')
    if b.get('ex'): note+=' The 97 W adapter caps the wall reading on this laptop (the battery covers the rest), so the efficiency is probably overstated.'
    if extra: note+=' '+extra
    r=dict(w='gpu',game=game,chip=chip,ck=chip.replace(' 14c',''),gen=b['gen'],dev=dev,tier=b['tier'],form=b['form'],
           x=fps,xlo=round(fps*math.exp(-SX),3),xhi=round(fps*math.exp(SX),3),e=round(e,5),elo=round(e*math.exp(-s),5),ehi=round(e*math.exp(s),5),
           p=P,plo=round(P*math.exp(-sP),1),phi=round(P*math.exp(sP),1),q='E',est=1,pe=1,seen=True,src=g+'_'+sk,resc=False,bench=bench,note=note)
    if b.get('ex'): r['ex']=1
    rows.append(r)
    D['sources'][g+'_'+sk]=dict(name=UN[sk]+' ('+game+')',url=U[sk])
D['est']+=rows
json.dump(D,open('data8.json','w'),separators=(',',':'))
for r in rows: print(r['game'][:8],r['chip'],r['dev'],r['x'],r['p'],r['e'],r['elo'],r['ehi'])
