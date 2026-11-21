"""-> data11.json  Small-model LLM sets from the oMLX Community Benchmarks (omlx_rows.json): Llama 3.2 3B and 1B 4-bit on
every chip, plus four Qwen sets with ten chips or more (Qwen3 1.7B 8-bit, 13 chips but 12 of them
single runs, is left out). Speeds are crowd-sourced medians (tok_s_robust); no power was
measured, so each chip reuses its Llama 2 7B decode-power estimate, widened by 10%, as llm2.py does for the sweeps."""
import json, math
D=json.load(open('data10.json')); O=json.load(open('omlx_rows.json'))['sets']
ll={r['chip']:r for r in D['est'] if r['w']=='llm' and r.get('src')=='llamacpp'}
GC={r['chip']:int(r['bench'].split(', ')[1].split('-core')[0]) for r in ll.values()}   # GPU cores of each chip's Llama 2 7B point
# (source model, quant) -> page model name, set, source key
SETS={('Llama 3.2 3B Instruct','MLX 4bit'):('Llama 3.2 3B 4-bit (oMLX)','omlx','omlx_l3b'),('Llama 3.2 1B Instruct','MLX 4bit'):('Llama 3.2 1B 4-bit (oMLX)','omlx','omlx_l1b'),
      ('Qwen2.5 0.5B Instruct','MLX 4bit'):('Qwen2.5 0.5B 4-bit (oMLX)','omlxq','omlx_q25_05'),('Qwen3 0.6B','MLX 4bit'):('Qwen3 0.6B 4-bit (oMLX)','omlxq','omlx_q3_06'),
      ('Qwen3 1.7B','MLX 4bit'):('Qwen3 1.7B 4-bit (oMLX)','omlxq','omlx_q3_17'),
      ('Qwen2.5 3B Instruct','MLX 4bit'):('Qwen2.5 3B 4-bit (oMLX)','omlxq','omlx_q25_3')}
EXTRA_P=0.10                       # extra log spread on power for borrowing it from the 7B run
sx=lambda n:0.04+0.15/math.sqrt(n) # speed spread of a crowd-sourced median of n runs (as for Blender Open Data medians)
VERSION={('omlx','M5 Pro'):'The 16-core GPU bin is faster here (151.4 tok/s, 6 runs) than this 20-core bin; part of that inversion is oMLX versions: 20-core runs on v0.4.4 scored 131 to 149, on v0.5.8 and later 122 to 128.'}
rows=[]; dropped=[]
for s in O:
    q=s['quant'].split(' (')[0]; model,setk,sk=SETS[(s['model'],q)]
    by={}
    for r in s['rows']: by.setdefault(r['chip'],[]).append(r)
    for c,vs in by.items():
        if c not in ll: dropped.append((model,c,'no Llama 2 7B power')); continue
        want=GC[c]; m=[v for v in vs if v['gpu_cores']==want]; r=m[0] if m else max(vs,key=lambda v:v['gpu_cores'])
        others=[v for v in vs if v is not r]
        for v in others: dropped.append((model,c,f"{v['gpu_cores']}-core GPU"))
        b=ll[c]; P=b['p']; sP=math.sqrt((math.log(b['phi']/b['plo'])/2)**2+EXTRA_P**2); n=r['n_robust']; sxx=sx(n); st=math.sqrt(sP*sP+sxx*sxx)
        x=r['tok_s_robust']; e=x/P; gc=r['gpu_cores']
        note=(f"Generation speed measured: crowd-sourced oMLX Community Benchmarks (MLX), the median of the {n} run{'s' if n>1 else ''} within 0.6 times the best run in the {c} {gc}-core GPU bin"
              +(f" ({r['n_runs']} runs in all, plain median {r['tok_s']:g} tok/s)" if r['n_runs']>n else '')+", 1k-token context. "
              "Submissions mix oMLX versions, macOS versions, memory sizes and chassis (oMLX does not record whether it is a MacBook or a desktop), so a bin can sit 10 to 20% off another. "
              f"No power was measured: wall power is this chip's Llama 2 7B decode-power estimate ({P:.0f} W, {b['plo']:g} to {b['phi']:g} W), widened by 10%, as for the context sweeps. "
              "A small model streams fewer bytes per token, so the GPU may draw less than with the 7B model and the efficiency here is more likely understated than overstated"
              +(", most of all for 1B on the big chips, which are limited by per-token latency rather than memory bandwidth" if '1B' in model or '0.' in model else '')+'.')
        if gc!=want: note+=f" Only a {gc}-core GPU bin exists for this chip, while the power estimate is for the {want}-core GPU, so the power may be a little {'low' if gc>want else 'high'}."
        if others: note+=' Left out: the '+', '.join(f"{v['gpu_cores']}-core GPU bin ({v['tok_s_robust']:g} tok/s, {v['n_robust']} run{'s' if v['n_robust']>1 else ''})" for v in others)+f", because this chip's power estimate is for the {want}-core GPU."
        if (setk,c) in VERSION and '3B' in model and 'Llama' in model: note+=' '+VERSION[(setk,c)]
        rows.append(dict(w='llm',chip=c,ck=c,gen=b['gen'],dev=b['dev'],tier=b['tier'],form=b['form'],model=model,set=setk,
            x=x,xlo=round(x*math.exp(-sxx),2),xhi=round(x*math.exp(sxx),2),e=round(e,4),elo=round(e*math.exp(-st),4),ehi=round(e*math.exp(st),4),
            p=P,plo=round(P*math.exp(-sP),1),phi=round(P*math.exp(sP),1),q='B' if n<=2 else 'E',est=1,pe=1,seen=True,src=sk,resc=False,
            bench=f"oMLX benchmark, {s['quant'].split(' (')[0]}, {gc}-core GPU, 1k-token context, median of {n} run{'s' if n>1 else ''}",note=note))
    D['sources'][sk]=dict(name=f"oMLX Community Benchmarks, {model.replace(' (oMLX)','')} (crowd-sourced; power estimated on this page)",url=s['url'])
D['est']+=rows
json.dump(D,open('data11.json','w'),separators=(',',':'))
for r in rows: print(f"{r['model']:26} {r['chip']:9} x={r['x']:6} n={r['bench'].split('median of ')[1]:8} P={r['p']:6} e={r['e']:.3f} q={r['q']}")
print(len(rows),'rows; dropped',len(dropped)); [print('  drop',d) for d in dropped]
