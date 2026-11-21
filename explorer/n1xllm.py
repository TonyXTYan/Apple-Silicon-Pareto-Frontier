"""-> data22.json  LLM generation on the NVIDIA N1X (RTX Spark) laptops, from n1xllm_rows.json (id = position in that list, each row
with the URL it was read from). Frandroid's Asus ProArt P16 review: one continuous Qwen3.6 35B-A3B run on battery with the whole
laptop's power read during the run (the only N1X LLM point with power of the same run), and four llama-bench runs plugged in;
StorageReview's Surface Laptop Ultra review: two Ollama generation rates from its Codex CLI agent test. Rows without power of their
own borrow it from the same laptop model's Cyberpunk 2077 wall power with the rule llm.py, nv2.py and mxfill.py use (decode wall
power = 0.75 to 1.1 times gaming wall power), widened because the unit differs from Notebookcheck's; they are est+pe, grade 'B'
(one outlet each, GGUF type not named). Model names match rows already on the page so they share frontiers (the frontier strips
' (oMLX)'). No GB10 (DGX Spark) value is relabelled as N1X, and no Llama 2 7B Q4_0 run exists for the N1X, so its matrix cell stays
empty (documented in mxfill_rows.json `gaps`)."""
import json, math
D=json.load(open('data21.json')); X={r['id']:r for r in json.load(open('n1xllm_rows.json'))['rows']}
url2key={v['url']:k for k,v in D['sources'].items()}
def src(u,name):
    if u not in url2key:
        k='n1x_'+str(len([k for k in D['sources'] if k.startswith('n1x_')])); D['sources'][k]=dict(name=name,url=u); url2key[u]=k
    return url2key[u]
N1='NVIDIA N1X (RTX Spark)'; PA,SU='Asus ProArt P16 H7607 (RTX Spark)','Microsoft Surface Laptop Ultra (2026)'
SD={PA:'ProArt P16',SU:'Surface Ultra'}
gpu=lambda dev: next(r for r in D['rows'] if r['w']=='gpu' and r['chip']==N1 and r['dev']==dev)
hw=lambda b: math.log(b['phi']/b['plo'])/2 if b.get('plo') else 0.05
LF=math.sqrt(0.75*1.1); LS=math.log(1.1/0.75)/2   # decode wall power = 0.75 to 1.1 times gaming wall power (llm.py, nv2.py, mxfill.py)
UNIT=0.05                                         # extra log spread: the speed was measured on another unit of the same laptop model
CHIP=('The N1X (RTX Spark) is a Windows-on-Arm laptop SoC with 20 Arm cores and a 6,144-core Blackwell GPU sharing 128 GB of LPDDR5X (about 273 to 300 GB/s), '
      'the GB10\'s design in a 45 to 80 W laptop envelope; no GB10 (DGX Spark) figure is used here.')
rows=[]; est=[]
def base(r,dev,bench,note):
    return dict(w='llm',chip=N1,dev=dev,tier='NVIDIA',form='laptop',x=r['x'],src=src(r['url'],r['src_name']),q='B',bench=bench,resc=False,note=note,sl='N1X',sd=SD[dev],model=r['model'])
def borrowed(i,sx,bench,how,extra=''):
    r=X[i]; b=gpu(r['dev']); s=math.sqrt(LS*LS+hw(b)**2+UNIT**2); x=r['x']; P=LF*b['p']; plo,phi=P*math.exp(-s),P*math.exp(s)
    note=(f"Generation speed measured: {how} {r['others']} No power was measured with this run: wall power is 0.75 to 1.1 times (central {LF:.2f}) the Cyberpunk 2077 wall power of the {r['dev']} "
          f"({b['p']:g} W, Notebookcheck), the rule the page uses for the Macs' decode power, widened by 5% because the speed comes from another unit. "+(extra+' ' if extra else '')+CHIP)
    o=base(r,r['dev'],bench,note)
    o.update(ck=N1,gen=0,xlo=round(x*math.exp(-sx),3),xhi=round(x*math.exp(sx),3),e=round(x/P,4),elo=round(x/phi*math.exp(-sx),4),ehi=round(x/plo*math.exp(sx),4),
             p=round(P,1),plo=round(plo,1),phi=round(phi,1),est=1,pe=1,seen=True,psrc=b['src'])
    est.append(o); return o

# ---- 0: the one run with its own power: continuous generation on battery, whole laptop
r=X[0]
o=base(r,PA,'llama.cpp CUDA, Qwen3.6-35B-A3B 4-bit, continuous 1,024-token answers on battery (whole-laptop power read by Windows)',
       'Generation speed and power from the same run: Frandroid chained 30 answers of 1,024 tokens (about 7 minutes) on battery in Performance mode and read the whole laptop\'s draw, '
       '89 to 93 W at 72 tok/s; the battery fell about 1.56% (of 99.9 Wh) a minute, which is 93.5 W, and the review gives 0.36 Wh per 1,000 tokens (0.77 tokens per joule). '
       'Weaker: the power is the battery side, read by Windows, with the internal display on, not a wall meter with an external monitor as for Notebookcheck\'s readings; it leaves out the charger\'s losses, so the power range runs from 89 W to 10% above the 93.5 W drain figure (102.9 W), what a wall reading could add. '
       'Plugged in, the same run held 75.2 to 76.8 tok/s with the GPU part at 43.8 W against 30.3 W on battery, so a plugged-in point would draw more. '+CHIP)
P,plo,phi=r['p_w'],r['p_lo'],round(1.1*r['p_hi'],1)   # top of the range: the drain figure plus up to 10% charger loss at the wall
o.update(e=round(r['x']/P,4),p=P,plo=plo,phi=phi,elo=round(r['x']/phi,4),ehi=round(r['x']/plo,4)); rows.append(o)

# ---- 1-4: llama-bench, plugged in (Frandroid); power from the ProArt P16's Cyberpunk wall power
FR='llama-bench (llama.cpp b11582) with CUDA, plugged in, Performance mode, a 4-bit GGUF whose type the review does not name ({q}); prompt processing {pp:,} tok/s.'
CHK=('Check: the same laptop drew 89 to 93 W on battery generating Qwen3.6 35B-A3B (the measured point), with the GPU part 13.5 W lower than plugged in, so about 105 W plugged in before the charger, inside this range. '
     'Frandroid\'s own wall meter read 114 to 138.4 W in Cyberpunk 2077 on its unit.')
for i in (1,2,3,4):
    r=X[i]; q=r['quant'].replace('4-bit, GGUF type not named, ','').replace(' file','')
    how=FR.format(q=q,pp=r['pp512']) if i!=4 else f"llama-bench (llama.cpp b11582) with CUDA, plugged in, Performance mode, MXFP4 ({r['quant'].split(', ')[1].replace(' file','')}); prompt processing {r['pp512']:,} tok/s."
    borrowed(i,0.05,f"llama.cpp b11582 llama-bench, CUDA, {r['model']} {'MXFP4' if i==4 else '4-bit'}",how,CHK)

# ---- 5-6: Ollama generation rates in StorageReview's Codex CLI agent test (Surface Laptop Ultra)
r=X[5]; borrowed(5,0.08,'Ollama (CUDA), gpt-oss:20b MXFP4, Codex CLI agent at 64K context, generation rate',
    'StorageReview\'s Codex CLI coding-agent test on Ollama with CUDA (native Arm64 build), gpt-oss:20b (natively MXFP4), 64K context, generation rate over the median of three runs, plugged in, Best performance mode. '
    'An agent run at long context, not a short llama-bench test.')
r=X[6]; borrowed(6,0.10,'Ollama (CUDA), Qwen3.6-35B-A3B, Codex CLI agent at 64K context, generation rate',
    'StorageReview\'s Codex CLI coding-agent test on Ollama with CUDA (native Arm64 build), Qwen3.6-35B-A3B (quantisation not stated, 21.1 GB file), 64K context, generation rate over the median of three runs, plugged in, Best performance mode.',
    'Weaker: the quantisation is not stated and the rate is 19% above Frandroid\'s llama-bench run of the model on the ProArt P16, so a 10% speed spread is allowed.')

# nothing here may land in the Llama 2 7B Q4_0 matrix column, or relabel a GB10 point
for o in rows+est: assert o['model']!='Llama 2 7B Q4_0' and o['chip']==N1
assert len(rows)+len(est)==len(X)==7
D['rows']+=rows; D['est']+=est
json.dump(D,open('data22.json','w'),separators=(',',':'))
for o in rows+est: print(f"{o['model'][:22]:22} {o['dev'][:36]:36} x={o['x']:<6} p={o['p']:<6} [{o.get('plo','')},{o.get('phi','')}] e={o['e']:<7} [{o.get('elo','')},{o.get('ehi','')}] q={o['q']} {'pe' if o.get('pe') else 'measured'}")
