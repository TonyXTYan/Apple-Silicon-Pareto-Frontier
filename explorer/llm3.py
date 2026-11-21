import json, math
D=json.load(open('data6.json'))
for r in D['est']:
    if r.get('sweep'): r['set']='sweep'; r['grp']=r['chip']+'|'+r['model']; r['ord']=r['ctx']
ll={r['chip']:r for r in D['est'] if r['w']=='llm' and r.get('src')=='llamacpp'}
rows=[]
def add(c,dev,form,model,eng,tg,P,Plo,Phi,src,bench,note,grp,ord_,extra_s=0.1,**kw):
    sP=math.sqrt((math.log(Phi/Plo)/2)**2+extra_s**2); sx=0.04; s=math.sqrt(sP*sP+sx*sx); e=tg/P
    rows.append(dict(w='llm',chip=c,ck=c,gen=int(c[1]),dev=dev,tier='Ultra' if 'Ultra' in c else 'Max' if 'Max' in c else 'Pro' if 'Pro' in c else 'base',form=form,model=model,eng=eng,
      x=tg,xlo=round(tg*math.exp(-sx),3),xhi=round(tg*math.exp(sx),3),e=round(e,5),elo=round(e*math.exp(-s),5),ehi=round(e*math.exp(s),5),p=round(P,1),plo=round(P*math.exp(-sP),1),phi=round(P*math.exp(sP),1),
      q='E',est=1,pe=1,seen=True,src=src,resc=False,bench=bench,note=note,grp=grp,ord=ord_,**kw))
# ---- MLX vs GGUF, same machine, same model
PAIRS=[('M3 Ultra','Qwen3.5 9B 4-bit',77.8,107.5,'tb','llama-bench tg128 Q4_K_M vs mlx-lm 4-bit'),
       ('M1 Ultra','Qwen3 8B 4-bit',62,78,'outl','128 new tokens after a 515-token prompt, 4,096-token context'),
       ('M4 Max','Qwen3 0.6B 4-bit',281.5,525.5,'groundy','4-bit both ways'),('M4 Max','Llama 3.2 1B 4-bit',331.3,461.9,'groundy','4-bit both ways'),
       ('M4 Max','Qwen3 4B 4-bit',118.2,159.0,'groundy','4-bit both ways'),('M4 Max','Qwen3 8B 4-bit',76.9,93.3,'groundy','4-bit both ways'),
       ('M4 Max','Qwen3.5 35B-A3B 4-bit',72,130,'antek','mixture of experts, about 3B active; MLX via the Python API')]
for c,m,g,x,src,how in PAIRS:
    b=ll[c]; P,Plo,Phi=b['p'],b['plo'],b['phi']; dev=b['dev']
    for eng,tg,o in (('llama.cpp (GGUF)',g,0),('MLX',x,1)):
        add(c,dev,b['form'],m,eng,tg,P,Plo,Phi,src,f'{eng}, {how}',
            f'Generation speed measured on one machine with both runtimes; wall power is this chip\'s decode-power estimate ({P:.0f} W) for both, widened by 10%. With the same power, the MLX to GGUF efficiency ratio equals the speed ratio ({x/g:.2f}x). If MLX pulls more memory bandwidth it may also draw a few percent more power, so the true ratio is likely a little smaller.',
            c+'|'+m+'|pair',o,set='mlx')
# ---- Mac clusters, Jeff Geerling, 4x M3 Ultra Mac Studio, RDMA over Thunderbolt 5 (exo 1.0) vs llama.cpp RPC
P1=(190,150,227)
CL=[('Qwen3 235B','exo (RDMA over TB5)',[(1,19.5),(2,26.2),(4,31.9)]),('Qwen3 235B','llama.cpp RPC',[(1,20.4),(2,17.2),(4,15.2)]),
    ('DeepSeek V3.1 671B','exo (RDMA over TB5)',[(1,21.1),(2,27.8),(4,32.5)]),('DeepSeek V3.1 671B','llama.cpp RPC',[(4,14.6)]),
    ('Kimi K2 Thinking 1T','exo (RDMA over TB5)',[(4,28.3)])]
for m,eng,pts in CL:
    for n,tg in pts:
        if n==1: P,Plo,Phi=P1
        elif 'RPC' in eng: P,Plo,Phi=190+25*(n-1),150+10*(n-1),227+45*(n-1)
        else: P,Plo,Phi=n*0.8*190,n*110,n*240
        add('M3 Ultra',f'Mac Studio x{n}' if n>1 else 'Mac Studio','desktop',m,eng,tg,P,Plo,Phi,'geer_rdma',f'{eng}, {n} node'+('s' if n>1 else ''),
            ('One M3 Ultra; wall power from Geerling\'s metered M3 Ultra decode runs (150 to 227 W).' if n==1 else
             f'Cluster of {n} M3 Ultra Mac Studios. Wall power estimated as {n} x 110 to 240 W (central {0.8*190:.0f} W per node): Geerling reports each node under 250 W, and in a split model each GPU is busy only part of each token.')+
            ' Speed from Jeff Geerling\'s RDMA over Thunderbolt 5 tests (December 2025).',
            'M3 Ultra|'+m+'|'+eng,n,set='cluster',nodes=n)
D['est']+=rows
S=D['sources']
S['tb']=dict(name='terminalbytes, Ollama vs llama.cpp vs MLX on a Mac Studio',url='https://terminalbytes.com/ollama-vs-llama-cpp-vs-mlx-mac-2026/')
S['outl']=dict(name='outlier.host, GGUF vs MLX timed on an M1 Ultra',url='https://outlier.host/vs/gguf-vs-mlx-model-formats/')
S['groundy']=dict(name='Groundy, MLX vs llama.cpp on Apple Silicon (M4 Max)',url='https://groundy.com/articles/mlx-vs-llamacpp-on-apple-silicon-which-runtime-to-use-for-local-llm-inference/')
S['antek']=dict(name='Ante Kapetanovic, Ollama vs llama.cpp vs MLX with Qwen3.5 35B (M4 Max)',url='https://antekapetanovic.com/blog/qwen3.5-apple-silicon-benchmark/')
S['geer_rdma']=dict(name='Jeff Geerling, 1.5 TB of VRAM on Mac Studio: RDMA over Thunderbolt 5',url='https://jeffgeerling.com/blog/2025/15-tb-vram-on-mac-studio-rdma-over-thunderbolt-5')
json.dump(D,open('data7.json','w'),separators=(',',':'))
for r in rows: print(r['set'],r['chip'],r['dev'],r['model'],r['eng'],r['x'],r['p'],round(r['e'],4),round(1/r['e'],1),'J/tok')
