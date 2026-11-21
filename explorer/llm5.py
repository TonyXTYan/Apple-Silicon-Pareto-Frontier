"""-> data15.json  Mid-size (12 to 50B) LLM sets, from omlx_mid_rows.json (each set with its source URL and notes):
oMLX Community Benchmarks (MLX 4-bit, 1k-token context) for gpt-oss 20B, Qwen3 14B and Qwen3.5 27B on every chip, and
eighteen other oMLX mid-size sets with eight chips or more (kept out of the every-model view, as llm4.py does for the Qwen
small sets); the llama.cpp gpt-oss guide thread (#15396, llama-bench tg128) on seven chips; and three wall readings:
Jeff Geerling's M3 Ultra Qwen3 32B and Llama 2 13B runs (227 W peak) and an M4 Pro Mac mini running Qwen3 32B at ~40 W.
Speed-only rows reuse the chip's Llama 2 7B decode-power estimate widened by 10%, exactly as llm4.py does."""
import json, math
D=json.load(open('data14.json')); O=json.load(open('omlx_mid_rows.json'))['sets']
ll={r['chip']:r for r in D['est'] if r['w']=='llm' and r.get('src')=='llamacpp'}
GC={r['chip']:int(r['bench'].split(', ')[1].split('-core')[0]) for r in ll.values()}   # GPU cores of each chip's Llama 2 7B point
EXTRA_P=0.10                       # extra log spread on power for borrowing it from the 7B run (as llm4.py)
sx=lambda n:0.04+0.15/math.sqrt(n) # speed spread of a crowd-sourced median of n runs (as llm4.py)
MOE='a mixture of experts that reads only its active experts per token'
# source model -> page model name, set, source key, extra note. Names match rows already on the page so the frontier
# (which strips ' (oMLX)') joins them: gpt-oss 20B, DeepSeek R1 14B, Qwen3 32B, Qwen3 30B-A3B, Qwen3.5 35B-A3B 4-bit.
SETS={'gpt-oss 20B (21B total / 3.6B active MoE)':('gpt-oss 20B (oMLX)','omlx','omlx_gpt20',f'gpt-oss 20B is {MOE} (3.6B of 21B), and oMLX runs it as MXFP4 experts with 8-bit other weights.'),
 'Qwen3 14B':('Qwen3 14B (oMLX)','omlx','omlx_q3_14',''),
 'Qwen3.5 27B (base + same-architecture Claude-4.6-Opus-Distilled fine-tune pooled)':('Qwen3.5 27B (oMLX)','omlx','omlx_q35_27','The runs pool the base model with a fine-tune of the same architecture.'),
 'Qwen3 30B-A3B (MoE; base + Instruct-2507 pooled)':('Qwen3 30B-A3B (oMLX)','omlxl','omlx_q3_30a3',f'This is {MOE} (about 3B active); base and Instruct-2507 runs are pooled.'),
 'DeepSeek-R1-Distill-Qwen 14B':('DeepSeek R1 14B (oMLX)','omlxl','omlx_r1_14','DeepSeek-R1-Distill-Qwen 14B.'),
 'Devstral Small 2 24B (2512)':('Devstral Small 2 24B (oMLX)','omlxl','omlx_dev24',''),
 'Qwen2.5-Coder 32B Instruct':('Qwen2.5-Coder 32B (oMLX)','omlxl','omlx_q25c_32',''),
 'DeepSeek-R1-Distill-Qwen 32B':('DeepSeek R1 32B (oMLX)','omlxl','omlx_r1_32','DeepSeek-R1-Distill-Qwen 32B.'),
 'Gemma 3 12B it (mostly QAT)':('Gemma 3 12B (oMLX)','omlxl','omlx_g3_12','Most runs use the QAT 4-bit weights.'),
 'Qwen2.5 14B Instruct':('Qwen2.5 14B (oMLX)','omlxl','omlx_q25_14',''),
 'Gemma 3 27B it (mostly QAT)':('Gemma 3 27B (oMLX)','omlxl','omlx_g3_27','Most runs use the QAT 4-bit weights.'),
 'Qwen3 32B':('Qwen3 32B (oMLX)','omlxl','omlx_q3_32',''),
 'Mistral Small 24B (2501/3.1/3.2 pooled)':('Mistral Small 24B (oMLX)','omlxl','omlx_ms24','The 2501, 3.1 and 3.2 releases are pooled.'),
 'Qwen2.5 32B Instruct':('Qwen2.5 32B (oMLX)','omlxl','omlx_q25_32',''),
 'Qwen3-Coder 30B-A3B Instruct (MoE)':('Qwen3-Coder 30B-A3B (oMLX)','omlxl','omlx_q3c_30a3',f'This is {MOE} (about 3B active).'),
 'Qwen3.5 35B-A3B (MoE)':('Qwen3.5 35B-A3B 4-bit (oMLX)','omlxl','omlx_q35_35a3',f'This is {MOE} (about 3B active).'),
 'Qwen3.6 35B-A3B (MoE)':('Qwen3.6 35B-A3B (oMLX)','omlxl','omlx_q36_35a3',f'This is {MOE} (about 3B active).'),
 'Qwen3.6 27B':('Qwen3.6 27B (oMLX)','omlxl','omlx_q36_27',''),
 'Qwen3.8 27B':('Qwen3.8 27B (oMLX)','omlxl','omlx_q38_27',''),
 'Gemma 4 31B it':('Gemma 4 31B (oMLX)','omlxl','omlx_g4_31',''),
 'Gemma 4 26B-A4B it (MoE)':('Gemma 4 26B-A4B (oMLX)','omlxl','omlx_g4_26a4',f'This is {MOE} (about 4B active).')}
# bins left out by hand: faster than the chip's memory bandwidth can stream the weights (about 17 GB at 4-bit for Gemma 4 31B on
# the M5's 153 GB/s, so at most about 9 tok/s), which points to speculative decoding the filters missed
IMPLAUSIBLE={('Gemma 4 31B it','M5'):'16.4 tok/s, about twice what 153 GB/s can stream for 17 GB of weights'}
def pnote(c,b,P,moe):
    return (f"No power was measured: wall power is this chip's Llama 2 7B decode-power estimate ({P:.0f} W, {b['plo']:g} to {b['phi']:g} W), widened by 10%, as for the small oMLX sets. "
            +("Only the active experts are read per token, so the memory system may be less busy than with the 7B model and the efficiency here is more likely understated than overstated." if moe else
              "A dense 12 to 32B model streams two to four times the bytes per token of the 7B model while staying memory-bound, so the draw should be close to the 7B run's, if anything a little higher."))
def cores_note(gc,want):
    if gc is None: return f" The GPU core count was not stated; the power estimate is for the {want}-core GPU."
    if gc==want: return ''
    return f" Only a {gc}-core GPU bin is used for this chip, while the power estimate is for the {want}-core GPU, so the power may be a little {'low' if gc>want else 'high'}."
def speed_row(c,x,n,gc,model,setk,sk,bench,note,q=None,eng=None):
    b=ll[c]; P=b['p']; sP=math.sqrt((math.log(b['phi']/b['plo'])/2)**2+EXTRA_P**2); sxx=sx(n); st=math.sqrt(sP*sP+sxx*sxx); e=x/P
    o=dict(w='llm',chip=c,ck=c,gen=b['gen'],dev=b['dev'],tier=b['tier'],form=b['form'],model=model,set=setk,
        x=x,xlo=round(x*math.exp(-sxx),2),xhi=round(x*math.exp(sxx),2),e=round(e,4),elo=round(e*math.exp(-st),4),ehi=round(e*math.exp(st),4),
        p=P,plo=round(P*math.exp(-sP),1),phi=round(P*math.exp(sP),1),q=q or ('B' if n<=2 else 'E'),est=1,pe=1,seen=True,src=sk,resc=False,bench=bench,note=note)
    if eng: o['eng']=eng
    return o
rows=[]; meas=[]; dropped=[]
for s in O:
    if not s['source_name'].startswith('oMLX'): continue
    model,setk,sk,extra=SETS[s['model']]; moe=MOE in extra
    by={}
    for r in s['rows']: by.setdefault(r['chip'],[]).append(r)
    for c,vs in by.items():
        if c not in ll: dropped.append((model,c,'no Llama 2 7B power')); continue
        if (s['model'],c) in IMPLAUSIBLE: dropped.append((model,c,IMPLAUSIBLE[(s['model'],c)])); continue
        sus=[v for v in vs if v.get('suspect')]; ok=[v for v in vs if not v.get('suspect')]
        for v in sus: dropped.append((model,c,f"{v['gpu_cores']}-core GPU suspect"))
        if not ok: continue
        want=GC[c]; m=[v for v in ok if v['gpu_cores']==want]; r=m[0] if m else max(ok,key=lambda v:v['gpu_cores'])
        others=[v for v in ok if v is not r]
        for v in others: dropped.append((model,c,f"{v['gpu_cores']}-core GPU"))
        n=r['n_robust']; x=r['tok_s_robust']; gc=r['gpu_cores']
        note=(f"Generation speed measured: crowd-sourced oMLX Community Benchmarks (MLX 4-bit), the median of the {n} run{'s' if n>1 else ''} within 0.7 to 1.3 times the median of the {c} {gc}-core GPU bin"
              +(f" ({r['n_runs']} runs in all, plain median {r['tok_s']:g} tok/s)" if r['n_runs']>n else '')+", 1k-token context. "+(extra+' ' if extra else '')+
              "Submissions mix oMLX versions, macOS versions, memory sizes and chassis (oMLX does not record whether it is a MacBook or a desktop), so a bin can sit 10 to 20% off another; "
              "runs implausibly fast for the chip's memory bandwidth (speculative decoding) were dropped before the median. "+pnote(c,ll[c],ll[c]['p'],moe)+cores_note(gc,want))
        if others: note+=' Left out: the '+', '.join(f"{v['gpu_cores']}-core GPU bin ({v['tok_s_robust']:g} tok/s, {v['n_robust']} run{'s' if v['n_robust']>1 else ''})" for v in others)+f", because this chip's power estimate is for the {want}-core GPU."
        if sus: note+=' Also left out as implausible for the chip (more than 40% off its tier): the '+', '.join(f"{v['gpu_cores']}-core GPU bin ({v['tok_s_robust']:g} tok/s)" for v in sus)+'.'
        rows.append(speed_row(c,x,n,gc,model,setk,sk,f"oMLX benchmark, {s['quant'].split(' (')[0]}, {gc}-core GPU, 1k-token context, median of {n} run{'s' if n>1 else ''}",note))
    D['sources'][sk]=dict(name=f"oMLX Community Benchmarks, {model.replace(' (oMLX)','').replace(' 4-bit','')} (crowd-sourced; power estimated on this page)",url=s['url'])
# ---- llama.cpp gpt-oss guide thread: llama-bench tg128 posts, one per chip; a separate engine set under the same model name
G=next(s for s in O if s['source_name'].startswith('llama.cpp GitHub discussion #15396'))
D['sources']['lcpp15396']=dict(name='llama.cpp discussion #15396, guide: running gpt-oss with llama.cpp (community llama-bench posts; power estimated on this page)',url=G['url'])
for r in G['rows']:
    c=r['chip']; gc=r.get('gpu_cores'); want=GC[c]; who=r['power_note'].replace('not measured; ','')
    thr='likely heat-throttled' in r['power_note']
    note=(f"Generation speed measured: one community llama-bench post (tg128, MXFP4 GGUF, Metal, flash attention on; {who}) in the llama.cpp gpt-oss guide thread. "
          "This is llama.cpp, not oMLX: compare it with the oMLX gpt-oss 20B points only loosely, since MLX usually decodes faster on the same chip. "
          +(f"The poster's machine: {r['device']}. " if r.get('device') else '')
          +("Georgi Gerganov judged this run heat-throttled, so it is graded C. " if thr else '')
          +pnote(c,ll[c],ll[c]['p'],True)+cores_note(gc,want))
    rows.append(speed_row(c,r['tok_s'],1,gc,'gpt-oss 20B','lcpp','lcpp15396',f"llama.cpp llama-bench, gpt-oss 20B MXFP4 GGUF, tg128{', '+str(gc)+'-core GPU' if gc else ''}",note,q='C' if thr else 'B',eng='llama.cpp'))
# ---- wall readings
J=next(s for s in O if s['source_name'].startswith('Jeff Geerling'))
D['sources']['geer_ai42']=dict(name='Jeff Geerling, ai-benchmarks, issue #42 (M3 Ultra Mac Studio, llama.cpp)',url='https://github.com/geerlingguy/ai-benchmarks/issues/42')
have={(r['chip'],r.get('model')) for r in D['rows'] if r['w']=='llm'}
for r in J['rows']:
    if not r.get('wall_w'): continue
    model={'DeepSeek-R1-Distill-Qwen 14B':'DeepSeek R1 14B','gpt-oss 20B (Q4_K_M GGUF)':'gpt-oss 20B','Qwen3 32B dense (file mislabeled 30B-A3B)':'Qwen3 32B','Llama 2 13B':'Llama 2 13B'}[r['model']]
    if (r['chip'],model) in have: continue                      # R1 14B and gpt-oss 20B are already on the page
    x=r['tok_s']; P=r['wall_w']
    note=('Power is the peak reading, so tokens per joule is a lower bound; it covers the whole llama-bench run, prompt processing included, and the instrument is not stated. '
          +("The file is named Qwen3-30B-A3B, but llama-bench reports a dense 32.76B-parameter qwen3 32B, and 26.69 tokens per second fits the dense model, not the 30B-A3B mixture of experts." if model=='Qwen3 32B' else ''))
    meas.append(dict(w='llm',chip='M3 Ultra',dev='Mac Studio',tier='Ultra',form='desktop',x=x,e=round(x/P,4),p=P,src='geer_ai42',q='B',
        bench=f"llama.cpp llama-bench (Metal), {model} Q4_K_M, tg128",resc=False,note=note.strip(),model=model,gen=3))
A=next(s for s in O if s['source_name'].startswith('Single-machine'))['rows'][0]
D['sources']['archy']=dict(name='Stephane Thirion, archy.net: Why my Mac mini M4 outperforms dual RTX 3090s for LLM inference',url='https://www.archy.net/why-my-mac-mini-m4-outperforms-dual-rtx-3090s-for-llm-inference')
meas.append(dict(w='llm',chip='M4 Pro',dev='Mac mini',tier='Pro',form='desktop',x=A['tok_s'],e=round(A['tok_s']/A['wall_w'],4),p=A['wall_w'],src='archy',q='C',
    bench='Ollama, Qwen3 32B (default quant, presumably Q4_K_M), 64 GB',resc=False,model='Qwen3 32B',gen=4,
    note='Power is the author\'s "~40 W power draw under load"; whether it is an average or a peak, and how it was measured, is not stated, so this is graded C. The CPU and GPU core counts are not stated either.'))
D['rows']+=meas; D['est']+=rows
json.dump(D,open('data15.json','w'),separators=(',',':'))
for r in meas+rows: print(f"{r['model']:28} {r['chip']:9} x={r['x']:7} P={r['p']:6} e={r['e']:.3f} q={r['q']}")
from collections import Counter
print(len(meas),'measured,',len(rows),'speed rows', dict(Counter(r['model'] for r in rows)))
print('dropped',len(dropped)); [print('  drop',d) for d in dropped]
