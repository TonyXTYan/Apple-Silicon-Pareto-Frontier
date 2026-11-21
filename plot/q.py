import matplotlib.pyplot as plt, numpy as np
C={'base':'#2a78d6','Pro':'#e0882a','Max':'#c0392b'}
# (label, tier, score, power W)   score ∝ jobs/s for a fixed scene
r15=[('M1','base',37.5*27.2,27.2),('M1 Pro','Pro',35.0*48.3,48.3),('M1 Max','Max',31.9*53,53),
     ('M2','base',42.4*29,29),('M2 Max','Max',28.5*72.8,72.8),('M3 Pro 11c','Pro',47.7*40.1,40.1),
     ('M3 Pro 12c','Pro',45.2*47.9,47.9)]
sc=[('M4 MBP14','base',174,12.8),('M4 Pro 12c MBP14','Pro',176,18.4),('M4 Pro 14c MBP14','Pro',177,16.0),
    ('M4 Pro 14c MBP16','Pro',178,18.7),('M4 Max MBP16','Max',178,21.6),('M5 MBP14','base',200,15.3),
    ('M5 Air 15','base',199,15.6),('M5 Pro MBP16','Pro',201,21.0),('M5 Max MBP14','Max',200,21.9),('M5 Max MBP16','Max',201,21.5)]
mc=[('M4 MBP14','base',986,39.8),('M4 Pro 12c MBP14','Pro',1435,65.7),('M4 Pro 14c MBP14','Pro',1662,73.6),
    ('M4 Pro 14c MBP16','Pro',1729,85.8),('M4 Max MBP16','Max',2069,92.2),('M5 MBP14','base',1172,42.6),
    ('M5 Air 15','base',962,27.6),('M5 Pro MBP16','Pro',2347,102),('M5 Max MBP14','Max',2073,84.1),('M5 Max MBP16','Max',2437,117.5)]
OFF={('M4–M5','M5 Max MBP14'):(5,6),('M4–M5','M5 Max MBP16'):(-6,2),('M4–M5','M5 Pro MBP16'):(-6,-10),('M4–M5','M4 Pro 14c MBP16'):(-6,6),('M4–M5','M4 Pro 12c MBP14'):(6,-10),('M4–M5','M5 MBP14'):(6,-10),
('M1–M3','M3 Pro 12c'):(-6,6)}
OFF2={'M5 Max MBP16':(-6,4),'M5 Pro MBP16':(-4,-13),'M4 Max MBP16':(6,6),'M5 Max MBP14':(6,-10),'M4 Pro 14c MBP14':(6,-10),'M4 Pro 14c MBP16':(6,6),'M4 Pro 12c MBP14':(6,4)}
fig,ax=plt.subplots(1,3,figsize=(18,6.2))
for a,(d,ref,title) in zip(ax,[(r15,'M1','M1–M3 · Cinebench R15 multi-core job'),
                                (sc,'M4 MBP14','M4–M5 · Cinebench 2024 single-thread job'),
                                (mc,'M4 MBP14','M4–M5 · Cinebench 2024 multi-core job')]):
    r=[x for x in d if x[0]==ref][0]; T0=1/r[2]; E0=r[3]/r[2]
    T=np.array([1/x[2]/T0 for x in d]); E=np.array([x[3]/x[2]/E0 for x in d])
    # iso-power lines: E = P*T
    tt=np.linspace(T.min()*.8,T.max()*1.15,50)
    for P in sorted({round(x[3]) for x in d})[::max(1,len(d)//4)]:
        a.plot(tt,(P/r[3])*tt,color='#bbb',lw=.7,ls='--',zorder=0)
        a.text(tt[-1],(P/r[3])*tt[-1],f' {P} W',fontsize=7,color='#999',va='center')
    for (n,t,_,_),x,y in zip(d,T,E):
        a.scatter(x,y,s=55,color=C[t],zorder=3,edgecolor='white')
        o=(OFF2.get(n,(5,4)) if 'multi-core job' in title and title.startswith('M4') else OFF.get((title[:5],n),(5,4))); a.annotate(n,(x,y),xytext=o,textcoords='offset points',fontsize=7.5,ha='right' if o[0]<0 else 'left')
    a.set_xlabel(f'time per job  (relative, {ref} = 1)   →  slower')
    a.set_ylabel(f'energy per job  (relative, {ref} = 1)   ↑  worse')
    a.set_title(title,fontsize=10); a.grid(alpha=.2); a.spines[['top','right']].set_visible(False)
from matplotlib.patches import Patch
fig.legend([Patch(color=c) for c in C.values()],['base','Pro','Max'],loc='upper right',frameon=False,ncol=3)
fig.suptitle('Energy to complete a fixed job vs time to complete it (whole-system wall power, Notebookcheck)',x=.01,ha='left',fontsize=12,weight='bold')
fig.text(.01,.005,'E_job = P·T, T ∝ 1/score. Dashed lines: constant average system power. Lower-left is better. Panels are different jobs; compare within a panel only. '
         'M3 Max omitted (no R15 power figure).',fontsize=8,color='#555')
fig.tight_layout(rect=(0,.03,1,.93)); fig.savefig('energy_per_job.png',dpi=150)
for d,ref in [(r15,'M1'),(sc,'M4 MBP14'),(mc,'M4 MBP14')]:
    r=[x for x in d if x[0]==ref][0]
    print(sorted([(round((x[3]/x[2])/(r[3]/r[2]),2),x[0]) for x in d]))
