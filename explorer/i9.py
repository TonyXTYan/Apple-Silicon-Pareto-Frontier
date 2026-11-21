import json, math
D=json.load(open('data4.json'))
C,DEV='Intel i9-9880H','MacBook Pro 16 (2019)'
base=dict(chip=C,ck=C,gen=0,tier='Intel',form='laptop')
def band(v,s): return round(v*math.exp(-s),4),round(v*math.exp(s),4)
rows=[]
# CPU all cores: measured. R23 8747/8758 (NBC) -> CB2024 via x86 ratio (i9-9880H avg R23 8657 -> CB2024 494, cpu-monkey; i9-9980HK 518 NBC)
P,Plo,Phi=85.2,68.4,103.0; x=8750*494/8657; sx=0.06
e=x/P; rows.append(dict(base,w='cpu-all',dev=DEV,x=round(x,1),xlo=round(x*math.exp(-sx),1),xhi=round(x*math.exp(sx),1),e=round(e,3),elo=round(x/Phi,3),ehi=round(x/Plo,3),p=P,plo=Plo,phi=Phi,
  bench='Cinebench R23 (8,750), rescaled for x86',resc=True,raw=8750,src='nbc_i9',q='A',
  note='Wall power is Notebookcheck\'s Cinebench R15 multi-core loop with an external monitor (85.2 W average, 68.4 to 103 W). The R23 score is converted to Cinebench 2024 with the ratio for this CPU (R23 8,657 to 2024 494, i9-9880H averages), not the Apple ratio used elsewhere, which would overstate it by about 20%; ±6% is allowed for that conversion.'))
# CPU one thread: R23 single 1140 (NBC) -> 2024 x 70/1162 ; power estimated
x=1140*70/1162; P,s=35.0,math.log(45/27)/2; sxx=0.07; st=math.sqrt(s*s+sxx*sxx); e=x/P
rows.append(dict(base,w='cpu-one',dev=DEV+' (estimate)',x=round(x,1),xlo=round(x*math.exp(-sxx),1),xhi=round(x*math.exp(sxx),1),e=round(e,3),elo=band(e,st)[0],ehi=band(e,st)[1],p=P,plo=27,phi=45,
  q='E',est=1,pe=1,seen=True,src='i9est',resc=True,raw=1140,bench='Cinebench R23 single (1,140), rescaled for x86; power estimated',
  note='Score measured (Notebookcheck R23 single 1,140, converted with the i9-9880H R23 to 2024 ratio). No single-thread wall power was published; 27 to 45 W is assumed: about 12 to 20 W at idle with the external monitor (which keeps the Radeon awake) plus about 15 to 25 W for one Coffee Lake core at 4.8 GHz.'))
# HPL: roofline estimate
x=256; sxx=math.log(330/180)/2; P=90; s=math.log(103/78)/2; st=math.sqrt(s*s+sxx*sxx); e=x/P
rows.append(dict(base,w='hpl',dev=DEV+' (estimate)',x=x,xlo=180,xhi=330,e=round(e,3),elo=band(e,st)[0],ehi=band(e,st)[1],p=P,plo=78,phi=103,q='E',est=1,pe=1,seen=True,src='i9est',resc=False,
  bench='Roofline estimate, not measured',note='No HPL run on this machine was found. Estimate: 8 cores x 16 double-precision FLOP per cycle (two AVX2 FMA units) x about 2.5 GHz sustained under AVX2 = 320 Gflops peak, at about 80% HPL efficiency = 256 Gflops (180 to 330). Wall power 78 to 103 W, since the 103 W charger caps whole-machine draw under heavy load.'))
# Blender CPU: Open Data 4.5 median for i9-9880H, power = 0.9-1.1 x Cinebench wall power
sc,n=127.15,35; x=sc/60; sxx=0.04+0.15/math.sqrt(n); s=math.sqrt((math.log(103/68.4)/2)**2+0.095**2); P=85.2; st=math.sqrt(s*s+sxx*sxx); e=x/P
rows.append(dict(base,w='bl-cpu',dev=DEV+' (estimate)',x=round(x,3),xlo=round(x*math.exp(-sxx),3),xhi=round(x*math.exp(sxx),3),e=round(e,4),elo=band(e,st)[0],ehi=band(e,st)[1],p=P,plo=round(P*math.exp(-s),1),phi=round(P*math.exp(s),1),
  q='E',est=1,pe=1,seen=True,src='blender',resc=False,bench=f'Blender 4.5 CPU, Open Data median {sc:,.0f} samples/min over {n} runs (all i9-9880H laptops)',
  note='Render speed measured (Blender Open Data, every i9-9880H laptop, Windows included); wall power 0.9 to 1.1 times the Cinebench loop wall power of this MacBook Pro 16.'))
# LLM: bandwidth roofline estimate, CPU inference
x=6.5; sxx=math.log(8.5/4.5)/2; P=70; s=math.log(90/55)/2; st=math.sqrt(s*s+sxx*sxx); e=x/P
rows.append(dict(base,w='llm',dev=DEV+' (estimate)',model='Llama 2 7B Q4_0',x=x,xlo=4.5,xhi=8.5,e=round(e,4),elo=band(e,st)[0],ehi=band(e,st)[1],p=P,plo=55,phi=90,q='E',est=1,pe=1,seen=True,src='i9est',resc=False,
  bench='Bandwidth estimate on the CPU, not measured',note='No llama.cpp run on this machine was found, and the Radeon Pro 5500M has too little memory for the model. Estimate: dual-channel DDR4-2666 gives 42.7 GB/s peak and roughly 30 GB/s in practice; each token reads the 3.6 GB of weights, so about 8 tok/s at most and 4.5 to 8.5 assumed. Wall power 55 to 90 W with all cores streaming memory.'))
D['rows']+= [rows[0]]; D['est']+=rows[1:]
D['sources']['nbc_i9']=dict(name='Notebookcheck, MacBook Pro 16 2019 i9 5500M review and i9-9880H data',url='https://www.notebookcheck.net/Apple-MacBook-Pro-16-2019-Laptop-Review-A-convincing-Core-i9-9880H-and-Radeon-Pro-5500M-powered-multimedia-laptop.445902.0.html')
D['sources']['i9est']=dict(name='Estimated on this page (see the point\'s note)',url='https://www.notebookcheck.net/Intel-Core-i9-9880H-Processor.416735.0.html')
json.dump(D,open('data5.json','w'),separators=(',',':'))
for r in rows: print(r['w'],r['x'],r['e'],r['elo'],r['ehi'],r['p'])
