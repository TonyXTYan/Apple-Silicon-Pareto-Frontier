import json, math
D=json.load(open('data5.json'))
ll={r['chip']:r for r in D['est'] if r['w']=='llm' and r.get('src')=='llamacpp'}
# XiongjieDai GPU-Benchmarks-on-LLM-Inference, Apple Silicon snapshot May 2024: tg over N generated tokens
T={('M1','7-core GPU, 8 GB'):{'Llama 3 8B Q4_K_M':[10.20,9.72,11.77,None]},
   ('M1 Max','32-core GPU, 64 GB'):{'Llama 3 8B Q4_K_M':[35.73,34.49,31.18,26.84],'Llama 3 8B F16':[18.75,18.43,16.33,15.03],'Llama 3 70B Q4_K_M':[4.34,4.09,4.09,3.71]},
   ('M2 Ultra','76-core GPU, 192 GB'):{'Llama 3 8B Q4_K_M':[78.81,76.28,64.58,54.13],'Llama 3 8B F16':[36.90,36.25,33.67,30.68],'Llama 3 70B Q4_K_M':[12.48,12.13,10.75,9.34],'Llama 3 70B F16':[4.76,4.71,4.48,4.23]},
   ('M3 Max','40-core GPU, 64 GB'):{'Llama 3 8B Q4_K_M':[48.97,50.74,44.21,36.12],'Llama 3 8B F16':[22.04,22.39,20.72,18.74],'Llama 3 70B Q4_K_M':[7.65,7.53,6.58,5.60]}}
GB={'Llama 3 8B Q4_K_M':4.92,'Llama 3 8B F16':16.07,'Llama 3 70B Q4_K_M':42.52,'Llama 3 70B F16':141.1}
NS=[512,1024,4096,8192]; rows=[]
for (c,cfg),mods in T.items():
    b=ll[c]; P,Plo,Phi=b['p'],b['plo'],b['phi']; sP=math.log(Phi/Plo)/2; sP=math.sqrt(sP**2+0.1**2); sx=0.05; s=math.sqrt(sP**2+sx**2)
    for m,v in mods.items():
        for n,tg in zip(NS,v):
            if tg is None: continue
            e=tg/P; bw=tg*GB[m]
            rows.append(dict(w='llm',chip=c,ck=c,gen=int(c[1]),dev=b['dev'],tier=b['tier'],form=b['form'],model=m,ctx=n,sweep=1,x=tg,xlo=round(tg*math.exp(-sx),3),xhi=round(tg*math.exp(sx),3),
              e=round(e,4),elo=round(e*math.exp(-s),4),ehi=round(e*math.exp(s),4),p=P,plo=round(P*math.exp(-sP),1),phi=round(P*math.exp(sP),1),q='E',est=1,pe=1,seen=True,src='xdai',resc=False,
              bench=f'llama-bench tg{n} ({n} tokens generated, so the context grows to {n:,}), {cfg}',
              note=f'Generation speed measured (XiongjieDai, May 2024 snapshot); wall power is the same estimate as this chip\'s Llama 2 7B point ({P:.0f} W), widened by 10% because decode power should change little with model size or context once memory bandwidth is saturated. Weights stream at about {bw:.0f} GB/s here.'))
D['est']+=rows
D['sources']['xdai']=dict(name='XiongjieDai, GPU benchmarks on LLM inference (llama.cpp); power estimated on this page',url='https://github.com/XiongjieDai/GPU-Benchmarks-on-LLM-Inference')
json.dump(D,open('data6.json','w'),separators=(',',':'))
print(len(rows))
for r in rows:
    if r['ctx']==512: print(r['chip'],r['model'],r['x'],r['p'],round(r['e'],3),round(1/r['e'],2),'J/tok', round(r['e']*{'Llama 3 8B Q4_K_M':8,'Llama 3 8B F16':8,'Llama 3 70B Q4_K_M':70.6,'Llama 3 70B F16':70.6}[r['model']],2),'Bparam-tok/J')
