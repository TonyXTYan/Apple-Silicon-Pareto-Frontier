import json, math
D=json.load(open('data2.json'))
# llama.cpp Apple Silicon thread (Llama 2 7B, Q4_0, tg128 / pp512), full-GPU variant of each chip
TG={'M1':(8,117.96,14.15),'M1 Pro':(16,266.25,36.41),'M1 Max':(32,530.06,61.19),'M1 Ultra':(64,1030.04,83.73),
    'M2':(10,179.57,21.91),'M2 Pro':(19,341.19,38.86),'M2 Max':(38,671.31,65.95),'M2 Ultra':(76,1238.48,94.27),
    'M3':(10,186.75,21.34),'M3 Pro':(18,341.67,30.74),'M3 Max':(40,759.70,66.31),'M3 Ultra':(80,1471.24,92.14),
    'M4':(10,221.29,24.11),'M4 Pro':(20,439.78,50.74),'M4 Max':(40,885.68,83.06),
    'M5':(10,722.79,31.88),'M5 Pro':(20,1620.64,66.33),'M5 Max':(40,3219.99,119.92),'M5 Ultra':(80,4944.66,179.10),'M6':(8,988.93,35.74)}
TIER=lambda c:'Ultra' if 'Ultra' in c else 'Max' if 'Max' in c else 'Pro' if 'Pro' in c else 'base'
# measured GPU-load wall power (Cyberpunk 2077, Notebookcheck): (device, form, avg, P1, max)
GPUW={'M4':('Mac mini','desktop',39.6,38.2,41),'M4 Pro':('MacBook Pro 14','laptop',80.5,78.7,83),'M4 Max':('MacBook Pro 16','laptop',119.3,115.7,126.9),
      'M5':('MacBook Pro 14','laptop',42.4,41.7,44.2),'M5 Pro':('MacBook Pro 16','laptop',79.8,74.6,81.6),'M5 Max':('MacBook Pro 16','laptop',136.7,133.6,141.8),'M6':('Mac mini','desktop',38.4,37.6,38.9)}
gpu_est={r['chip']:r for r in D['est'] if r['w']=='gpu' and not r.get('mode')}
F,FLO,FHI=0.9,0.75,1.1          # decode wall power as a fraction of GPU-load wall power (calibration in the note)
M3U=(190,150,227)               # M3 Ultra decode wall power, from Geerling's metered llama.cpp runs (peak 223 to 262 W)
rows=[]
for c,(gc,pp,tg) in TG.items():
    if c=='M3 Ultra': P,Plo,Phi=M3U; dev,form='Mac Studio','desktop'; how='Decode wall power taken from Jeff Geerling\'s metered M3 Ultra llama.cpp runs (peak 223 to 262 W; 150 to 227 W assumed for the average).'
    elif 'Ultra' in c:
        g=gpu_est[c]; s=g['p']/gpu_est['M3 Ultra']['p']; P=M3U[0]*s; Plo,Phi=P/1.5,P*1.5; dev,form='Mac Studio','desktop'
        how=f'Decode wall power scaled from the metered M3 Ultra by the model\'s GPU-power ratio ({s:.2f}), with a factor-of-1.5 range.'
    elif c in GPUW:
        dev,form,a,lo,hi=GPUW[c]; P,Plo,Phi=F*a,FLO*lo,FHI*hi
        how=f'Decode wall power = 0.75 to 1.1 times the measured Cyberpunk 2077 wall power of the {dev} ({a} W, Notebookcheck).'
    else:
        g=gpu_est[c]; gp=g['p']; glo=g['x']/g['ehi']; ghi=g['x']/g['elo']; P,Plo,Phi=F*gp,FLO*glo,FHI*ghi; dev,form=g['dev'].replace(' (estimate)',''),g['form']
        how=f'Decode wall power = 0.75 to 1.1 times the model\'s estimated GPU-load wall power ({gp:.0f} W, itself uncertain by about 40%).'
    e=tg/P
    rows.append(dict(w='llm',chip=c,ck=c,gen=int(c[1]),dev=dev+' (estimate)',tier=TIER(c),form=form,model='Llama 2 7B Q4_0',x=tg,e=round(e,4),elo=round(tg/Phi,4),ehi=round(tg/Plo,4),
        p=round(P,1),plo=round(Plo,1),phi=round(Phi,1),q='E',est=1,seen=True,bench=f'llama.cpp tg128, {gc}-core GPU; prompt processing {pp:,.0f} tok/s',src='llamacpp',resc=False,
        note='Generation speed measured (llama.cpp Apple Silicon thread); wall power estimated. '+how+' The 0.75 to 1.1 factor comes from the two machines with both readings: the M4 Mac mini peaked at 30.1 W generating with Llama 3.2 3B against 39.6 W in Cyberpunk (0.76), and MindStudio saw 38 W on the M6 Mac mini against 38.4 W (about 1.0).'))
D['est']=[r for r in D['est'] if not (r['w']=='llm')]+rows
D['sources']['llamacpp']=dict(name='llama.cpp Apple Silicon performance thread; power estimated on this page',url='https://github.com/ggml-org/llama.cpp/discussions/4167')
json.dump(D,open('data3.json','w'),separators=(',',':'))
for r in sorted(rows,key=lambda r:-r['e']): print(f"{r['chip']:9s} {r['x']:7.1f} tok/s  P={r['p']:6.1f} [{r['plo']},{r['phi']}]  {r['e']:.3f} tok/J  {1/r['e']:.2f} J/tok")
