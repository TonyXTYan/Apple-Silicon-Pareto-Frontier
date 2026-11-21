"""-> data16.json  Small-variant LLM sets from omlx_more_rows.json (oMLX Community Benchmarks, MLX 4-bit, 1k-token context):
Qwen3.5 0.8B, 2B, 4B and 9B, Qwen3.8 9B, Gemma 3 1B and 4B, Gemma 3n E4B, Gemma 4 E4B and E2B (small, set 'omlxq') and Gemma 4 12B
(mid-size, 'omlxl'), each with eight chips or more. Rules are llm4.py's and llm5.py's: the robust median of the bin that matches the
chip's Llama 2 7B point, suspect bins skipped, power = that chip's Llama 2 7B decode estimate widened by 10%, grade 'B' for up to two runs.
New here: a bandwidth check that drops any bin faster than the chip's rated memory bandwidth could stream the model's 4-bit weights."""
import json, math
D=json.load(open('data15.json')); O=json.load(open('omlx_more_rows.json'))['sets']
ll={r['chip']:r for r in D['est'] if r['w']=='llm' and r.get('src')=='llamacpp'}
GC={r['chip']:int(r['bench'].split(', ')[1].split('-core')[0]) for r in ll.values()}   # GPU cores of each chip's Llama 2 7B point
EXTRA_P=0.10                       # extra log spread on power for borrowing it from the 7B run (as llm4.py)
sx=lambda n:0.04+0.15/math.sqrt(n) # speed spread of a crowd-sourced median of n runs (as llm4.py)
# rated memory bandwidth (GB/s) per chip and GPU-core bin; chips not listed (M6) are not checked
BW={'M1':68,'M1 Pro':200,'M1 Max':400,'M1 Ultra':800,'M2':100,'M2 Pro':200,'M2 Max':400,'M2 Ultra':800,'M3':100,'M3 Pro':150,('M3 Max',30):300,('M3 Max',40):400,
    'M3 Ultra':819,'M4':120,'M4 Pro':273,('M4 Max',32):410,('M4 Max',40):546,'M5':153,'M5 Pro':307,('M5 Max',32):460,('M5 Max',40):614,'M5 Ultra':1228}
bw=lambda c,gc:BW.get((c,gc)) or BW.get(c)
# source model -> page model name, set, source key, a lower bound on the GB of 4-bit weights streamed per token (non-embedding weights; bandwidth check), extra note. Names carry the size ("NNB"),
# which the page's size chips parse. Qwen3.5 9B keeps '4-bit' to share a frontier with the MLX-vs-GGUF Qwen3.5 9B rows already on the page.
EFF='Per-layer embeddings are looked up rather than streamed, so the bytes read per token follow the effective size, not the raw parameter count.'
SETS={'Qwen3.5 0.8B':('Qwen3.5 0.8B (oMLX)','omlxq','omlx_q35_08',0.4,''),
 'Qwen3.5 2B':('Qwen3.5 2B (oMLX)','omlxq','omlx_q35_2',1.0,''),
 'Qwen3.5 4B':('Qwen3.5 4B (oMLX)','omlxq','omlx_q35_4',2.2,''),
 'Qwen3.5 9B':('Qwen3.5 9B 4-bit (oMLX)','omlxq','omlx_q35_9',4.4,''),
 'Qwen3.8 9B':('Qwen3.8 9B (oMLX)','omlxq','omlx_q38_9',4.4,''),
 'Gemma 3 1B it (mostly QAT)':('Gemma 3 1B (oMLX)','omlxq','omlx_g3_1',0.55,'Most runs use the QAT 4-bit weights.'),
 'Gemma 3 4B it (mostly QAT)':('Gemma 3 4B (oMLX)','omlxq','omlx_g3_4',2.2,'Most runs use the QAT 4-bit weights.'),
 'Gemma 3n E4B it (4B effective of 8B raw)':('Gemma 3n E4B (oMLX)','omlxq','omlx_g3n_e4',2.0,'Gemma 3n E4B has about 8B raw parameters but 4B effective. '+EFF),
 'Gemma 4 E4B it (4B effective)':('Gemma 4 E4B (oMLX)','omlxq','omlx_g4_e4',2.0,'Gemma 4 E4B is a 4B-effective model with larger raw size. '+EFF),
 'Gemma 4 E2B it (2B effective)':('Gemma 4 E2B (oMLX)','omlxq','omlx_g4_e2',1.0,'Gemma 4 E2B is a 2B-effective model with larger raw size. '+EFF),
 'Gemma 4 12B it':('Gemma 4 12B (oMLX)','omlxl','omlx_g4_12',6.0,'')}
def pnote(c,b,P,gb):
    return (f"No power was measured: wall power is this chip's Llama 2 7B decode-power estimate ({P:.0f} W, {b['plo']:g} to {b['phi']:g} W), widened by 10%, as for the other oMLX sets. "
            +("A small model streams fewer bytes per token than the 7B run, so the GPU may draw less and the efficiency here is more likely understated than overstated, most of all on the big chips, which are then limited by per-token latency rather than memory bandwidth."
              if gb<4 else "A 4-bit model of this size streams about as many bytes per token as the 7B run, so the draw should be close to the 7B run's."))
def cores_note(gc,want):
    if gc is None: return f" The GPU core count was not stated; the power estimate is for the {want}-core GPU."
    if gc==want: return ''
    return f" Only a {gc}-core GPU bin is used for this chip, while the power estimate is for the {want}-core GPU, so the power may be a little {'low' if gc>want else 'high'}."
rows=[]; dropped=[]
for s in O:
    model,setk,sk,gb,extra=SETS[s['model']]; srows=[]
    by={}
    for r in s['rows']: by.setdefault(r['chip'],[]).append(r)
    for c,vs in by.items():
        if c not in ll: dropped.append((model,c,'no Llama 2 7B power')); continue
        sus=[v for v in vs if v.get('suspect')]; ok=[v for v in vs if not v.get('suspect')]
        for v in sus: dropped.append((model,c,f"{v['gpu_cores']}-core GPU suspect"))
        # bandwidth check: tok/s x GB per token cannot exceed the rated memory bandwidth
        fast=[v for v in ok if bw(c,v['gpu_cores']) and v['tok_s_robust']*gb>bw(c,v['gpu_cores'])]
        for v in fast: dropped.append((model,c,f"{v['gpu_cores']}-core GPU {v['tok_s_robust']} tok/s x {gb} GB > {bw(c,v['gpu_cores'])} GB/s"))
        ok=[v for v in ok if v not in fast]
        if not ok: continue
        want=GC[c]; m=[v for v in ok if v['gpu_cores']==want]; r=m[0] if m else max(ok,key=lambda v:v['gpu_cores'] or 0)
        others=[v for v in ok if v is not r]
        for v in others: dropped.append((model,c,f"{v['gpu_cores']}-core GPU"))
        n=r['n_robust']; x=r['tok_s_robust']; gc=r['gpu_cores']; b=ll[c]; P=b['p']
        sP=math.sqrt((math.log(b['phi']/b['plo'])/2)**2+EXTRA_P**2); sxx=sx(n); st=math.sqrt(sP*sP+sxx*sxx); e=x/P
        note=(f"Generation speed measured: crowd-sourced oMLX Community Benchmarks (MLX 4-bit), the median of the {n} run{'s' if n>1 else ''} within 0.7 to 1.3 times the median of the {c} {str(gc)+'-core GPU bin' if gc else 'bin (GPU cores not stated)'}"
              +(f" ({r['n_runs']} runs in all, plain median {r['tok_s']:g} tok/s)" if r['n_runs']>n else '')+", 1k-token context. "+(extra+' ' if extra else '')+
              "Submissions mix oMLX versions, macOS versions, memory sizes and chassis (oMLX does not record whether it is a MacBook or a desktop), so a bin can sit 10 to 20% off another; "
              "runs implausibly fast for the chip's memory bandwidth (speculative decoding) were dropped before the median. "+pnote(c,b,P,gb)+cores_note(gc,want))
        if others: note+=' Left out: the '+', '.join(f"{v['gpu_cores']}-core GPU bin ({v['tok_s_robust']:g} tok/s, {v['n_robust']} run{'s' if v['n_robust']>1 else ''})" for v in others)+f", because this chip's power estimate is for the {want}-core GPU."
        if 'WIDE SPREAD' in r['power_note']: note+=f" The runs in this bin are widely spread ({r['tok_s_min']:g} to {r['tok_s_max']:g} tok/s), so the median is less certain than its run count suggests."
        if sus: note+=' Also left out as implausible for the chip (more than 40% off its tier): the '+', '.join(f"{v['gpu_cores']}-core GPU bin ({v['tok_s_robust']:g} tok/s)" for v in sus)+'.'
        if fast: note+=' Also left out: a bin faster than the memory bandwidth could stream the weights: '+', '.join(f"{v['gpu_cores']}-core GPU ({v['tok_s_robust']:g} tok/s)" for v in fast)+'.'
        srows.append(dict(w='llm',chip=c,ck=c,gen=b['gen'],dev=b['dev'],tier=b['tier'],form=b['form'],model=model,set=setk,
            x=x,xlo=round(x*math.exp(-sxx),2),xhi=round(x*math.exp(sxx),2),e=round(e,4),elo=round(e*math.exp(-st),4),ehi=round(e*math.exp(st),4),
            p=P,plo=round(P*math.exp(-sP),1),phi=round(P*math.exp(sP),1),q='B' if n<=2 else 'E',est=1,pe=1,seen=True,src=sk,resc=False,
            bench=f"oMLX benchmark, MLX 4bit, {str(gc)+'-core GPU' if gc else 'GPU cores not stated'}, 1k-token context, median of {n} run{'s' if n>1 else ''}",note=note))
    if len(srows)<8: dropped.append((model,'ALL',f'only {len(srows)} chips: set not used')); continue
    rows+=srows
    D['sources'][sk]=dict(name=f"oMLX Community Benchmarks, {model.replace(' (oMLX)','').replace(' 4-bit','')} (crowd-sourced; power estimated on this page)",url=s['url'])
D['est']+=rows
json.dump(D,open('data16.json','w'),separators=(',',':'))
from collections import Counter
for r in rows: print(f"{r['model']:26} {r['chip']:9} x={r['x']:7} P={r['p']:6} e={r['e']:.3f} q={r['q']}")
print(len(rows),'speed rows',dict(Counter(r['model'] for r in rows)))
print('dropped',len(dropped)); [print('  drop',d) for d in dropped]
