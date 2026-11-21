import json, re, io, contextlib, os
src=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','plot','all.py')).read().split("SURF=")[0].replace("apple_silicon_efficiency_data.csv","/tmp/_x.csv")
g={}
with contextlib.redirect_stdout(io.StringIO()): exec(src,g)
rows,pts,ref,sig=g['rows'],g['pts'],g['ref'],g['sig']
DEV={'MBP13':'MacBook Pro 13','MBP14':'MacBook Pro 14','MBP16':'MacBook Pro 16','Air 13':'MacBook Air 13','Air 15':'MacBook Air 15',
     'Air 13 8c-GPU':'MacBook Air 13 (8-core GPU)','Air 13 10c-GPU':'MacBook Air 13 (10-core GPU)','mini':'Mac mini','Studio':'Mac Studio'}
def cbsrc(chip,dev,b):
    if b=='R23':
        if dev=='mini': return 'nbc_mini_m4pro' if 'M4' in chip else 'nbc_mini_m4'
        if dev=='Studio': return 'nbc_studio23' if chip=='M2 Max' else 'nbc_m2pm'
        if chip.startswith('M3'): return 'nbc_m3' if chip=='M3' else 'nbc_m3pm'
        if chip=='M2 Max' or '10c-GPU' in dev: return 'nbc_m2pm'
        return 'nbc_m3'
    if dev=='mini': return 'nbc_mini_m6'
    if chip in('M3','M6') or (chip=='M4' and 'Air' in dev): return 'nbc_m6'
    if chip in('M4','M5') and dev=='MBP14': return 'nbc_m5'
    if chip.startswith('M4 Pro') and dev=='MBP14': return 'nbc_m6'
    return 'nbc_m5pm'
out=[]
for i,(chip,dev,tier,form,b,Sm,Sr,Pm,Ss,Ps) in enumerate(rows):
    for j,(job,P) in enumerate((('cpu-all',Pm),('cpu-one',Ps))):
        p=pts[2*i+j]
        out.append(dict(w=job,chip=chip,dev=DEV[dev],tier=tier,form=form,x=round(p['x'],1),xlo=round(p['xlo'],1),xhi=round(p['xhi'],1),
            e=round(p['y']*ref,3),elo=round(p['lo']*ref,3),ehi=round(p['hi']*ref,3),p=P[0],plo=P[1],phi=P[2],
            bench='Cinebench 2024' if b=='CB24' else 'Cinebench R23, rescaled',resc=b=='R23',raw=p['S'],src=cbsrc(chip,dev,b),q='A'))
L,F,D='laptop','fanless','desktop'
def add(w,chip,dev,tier,form,x,P,src,q='A',bench='',note='',model='',e=None):
    P=P if isinstance(P,tuple) else (P,None,None)
    e=e if e is not None else x/P[0]; x=x if x is not None else e*P[0]
    r=dict(w=w,chip=chip,dev=dev,tier=tier,form=form,x=round(x,2),e=round(e,4),p=P[0],src=src,q=q,bench=bench,resc=False)
    if P[1]: r.update(plo=P[1],phi=P[2],elo=round(e*P[0]/P[2],4),ehi=round(e*P[0]/P[1],4))
    if note: r['note']=note
    if 'overstated' in note: r['ex']=1
    if model: r['model']=model
    out.append(r)
H='HPL (High Performance Linpack)'
add('hpl','M4','Mac mini','base',D,299.93,39.6,'geer_hpl',bench=H)
add('hpl','M3 Ultra','Mac Studio','Ultra',D,1278.6,213,'geer_hpl',bench=H)
add('hpl','M4 Max','Mac Studio','Max',D,685.0,120,'geer_hpl',bench=H)
add('hpl','M1 Max','Mac Studio','Max',D,264.32,66,'geer_hpl',bench=H)
add('hpl','A18 Pro','MacBook Neo','base',F,57.012,10.6,'geer_hpl',bench=H,note='A-series chip. A laptop, so its own display may be included in the wall power.')
G='Cyberpunk 2077, 1080p ultra'
add('gpu','M5','MacBook Air 13','base',F,None,(17.7,17.4,18.2),'nbc_m5air',bench=G,e=1.107)
add('gpu','M5','MacBook Pro 14','base',L,None,(42.4,41.7,44.2),'nbc_m5gpu',bench=G,e=.686)
add('gpu','M5 Pro','MacBook Pro 16','Pro',L,None,(79.8,74.6,81.6),'nbc_m5gpu',bench=G,e=.672)
add('gpu','M5 Max','MacBook Pro 16','Max',L,None,(136.7,133.6,141.8),'nbc_m5gpu',bench=G,e=.681)
add('gpu','M5 Max','MacBook Pro 14','Max',L,None,(86.4,83.8,88.7),'nbc_m5gpu',q='B',bench=G,e=.926,note="Notebookcheck says this laptop's wall readings were affected by its power supply, so the efficiency is probably overstated.")
add('gpu','M4 Max','MacBook Pro 16','Max',L,None,(119.3,115.7,126.9),'nbc_m5gpu',bench=G,e=.657)
add('gpu','M4 Pro 14c','MacBook Pro 14','Pro',L,None,(80.5,78.7,83),'nbc_m5air',bench=G,e=.4547)
add('gpu','M4','Mac mini','base',D,None,(39.6,38.2,41),'nbc_mini_m6',bench=G,e=.4798)
add('gpu','M6','Mac mini','base',D,None,(38.4,37.6,38.9),'nbc_mini_m6',bench=G,e=.94)
pk='Power is the peak reading, so tokens per joule is a lower bound.'
for model,tps,W in (('Llama 3.2 3B',154.60,223),('gpt-oss 20B',115.29,227),('DeepSeek R1 14B',51.85,227),('Llama 3.1 70B',14.08,243),('DeepSeek R1 671B',19.89,261.8),('Llama 3.1 405B',1.96,256.4)):
    add('llm','M3 Ultra','Mac Studio','Ultra',D,tps,W,'geer_ai',q='B',bench='llama.cpp / Ollama',note=pk,model=model)
add('llm','M4','Mac mini','base',D,41.31,30.1,'geer_ai',q='B',bench='llama.cpp / Ollama',note=pk,model='Llama 3.2 3B')
ms='Power is a maximum under GPU load and the measuring method is not stated.'
add('llm','M4','Mac mini','base',D,18,44,'mindstudio',q='C',bench='llama.cpp',note=ms,model='9B model, Q4')
add('llm','M6','Mac mini','base',D,26.9,38,'mindstudio',q='C',bench='llama.cpp',note=ms,model='9B model, Q4')
N='https://www.notebookcheck.net/'
sources={
 'nbc_m3':('Notebookcheck, M3 analysis',N+'Apple-M3-SoC-analyzed-Increased-performance-and-improved-efficiency.766789.0.html'),
 'nbc_m3pm':('Notebookcheck, M3 Pro and M3 Max analysis',N+'Apple-M3-Pro-M3-Max-analysis-Apple-has-significantly-upgraded-its-Max-CPU.782974.0.html'),
 'nbc_m2pm':('Notebookcheck, M2 Pro and M2 Max analysis',N+'Apple-M2-Pro-and-M2-Max-analysis-GPU-is-more-efficient-the-CPU-not-always.699140.0.html'),
 'nbc_m5':('Notebookcheck, M5 analysis',N+'Analysis-of-the-Apple-M5-SoC-Apple-silicon-extends-its-lead-over-AMD-Intel-and-Qualcomm.1144213.0.html'),
 'nbc_m5pm':('Notebookcheck, M5 Pro and M5 Max CPU analysis',N+'Apple-M5-Pro-M5-Max-CPU-Analysis-M5-Max-is-not-much-faster-than-the-M4-Max.1246054.0.html'),
 'nbc_m6':('Notebookcheck, M6 analysis',N+'Apple-M6-SoC-Analysis-Apple-s-2-nm-chip-crushes-AMD-Intel-Qualcomm.1404057.0.html'),
 'nbc_mini_m4':('Notebookcheck, Mac mini M4 review',N+'Apple-Mac-Mini-M4-review-Smaller-faster-and-louder.918832.0.html'),
 'nbc_mini_m4pro':('Notebookcheck, Mac mini M4 Pro review',N+'Apple-Mac-Mini-M4-Pro-review-The-compact-and-frugal-desktop-PC-with-top-performance-and-expensive-upgrades.946883.0.html'),
 'nbc_mini_m6':('Notebookcheck, Mac mini 2026 (M6) review',N+'Compact-powerhouse-with-the-2-nm-M6-SoC-Apple-Mac-mini-2026-Review.1401148.0.html'),
 'nbc_studio23':('Notebookcheck, Mac Studio 2023 review',N+'Apple-Mac-Studio-2023-review-The-M2-Max-also-impresses-in-a-desktop-device.752807.0.html'),
 'nbc_m5gpu':('Notebookcheck, M5 Pro and M5 Max GPU analysis',N+'Apple-M5-Pro-M5-Max-GPU-Analysis-M5-Max-GPU-on-par-with-the-GeForce-RTX-5070-and-faster-than-Strix-Halo.1246060.0.html'),
 'nbc_m5air':('Notebookcheck, MacBook Air 13 M5 gaming efficiency',N+'Apple-s-entry-level-M5-SoC-in-the-MacBook-Air-13-only-consumes-7-8-Watts-in-games-like-Cyberpunk-2077-or-Baldur-s-Gate-3.1244916.0.html'),
 'geer_hpl':('Jeff Geerling, top500-benchmark','https://github.com/geerlingguy/top500-benchmark'),
 'geer_ai':('Jeff Geerling, ai-benchmarks','https://github.com/geerlingguy/ai-benchmarks'),
 'mindstudio':('MindStudio, M6 Mac mini local AI tests','https://www.mindstudio.ai/blog/m6-mac-mini-local-ai-performance'),
}
data=dict(rows=out,sources={k:dict(name=v[0],url=v[1]) for k,v in sources.items()},stitch=dict(all=round(sig['m']*100),one=round(sig['s']*100)))
json.dump(data,open('data.json','w'),separators=(',',':'))
print(len(out),'rows'); import collections; print(collections.Counter(r['w'] for r in out))
for r in out:
    if r['w'] in('hpl','gpu','llm'): print(r['w'],r['chip'],r['dev'],r.get('model',''),r['x'],r['e'],r['p'])
