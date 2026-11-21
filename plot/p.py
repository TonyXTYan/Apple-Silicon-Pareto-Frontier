import matplotlib.pyplot as plt
C={'base':'#2a78d6','Pro':'#e0882a','Max':'#c0392b'}
r15=[('M1','base',37.5),('M1 Pro','Pro',35.0),('M1 Max','Max',31.9),('M2','base',42.4),
     ('M2 Max','Max',28.5),('M3 Pro 11c','Pro',47.7),('M3 Pro 12c','Pro',45.2),('M3 Max 16c','Max',35.9)]
cb=[('M4\nMBP14','base',13.6,24.8),('M4 Pro 12c\nMBP14','Pro',9.24,21.8),('M4 Pro 14c\nMBP14','Pro',11.1,22.6),
    ('M4 Pro 14c\nMBP16','Pro',9.52,20.2),('M4 Max\nMBP16','Max',8.24,22.4),('M5\nMBP14','base',13.1,27.5),
    ('M5\nAir 15','base',12.8,34.9),('M5 Pro\nMBP16','Pro',9.57,23.0),('M5 Max\nMBP14','Max',9.13,24.6),('M5 Max\nMBP16','Max',9.35,20.7)]
fig,ax=plt.subplots(1,3,figsize=(17,5.6),gridspec_kw={'width_ratios':[1,1.3,1.3]})
for a in ax: a.spines[['top','right']].set_visible(False); a.grid(axis='y',alpha=.25)
a=ax[0]; x=range(len(r15))
a.bar(x,[v for *_,v in r15],color=[C[t] for _,t,_ in r15])
for i,(_,_,v) in enumerate(r15): a.text(i,v+.6,f'{v:g}',ha='center',fontsize=8)
a.set_xticks(list(x),[n for n,*_ in r15],rotation=45,ha='right',fontsize=8)
a.set_title('M1–M3: Cinebench R15 multi\n(points / W, whole system)',fontsize=10); a.set_ylabel('points per watt')
for k,(i,key) in enumerate([(1,2),(2,3)]):
    a=ax[i]; x=range(len(cb)); vals=[r[key] for r in cb]
    a.bar(x,vals,color=[C[r[1]] for r in cb])
    for j,v in enumerate(vals): a.text(j,v+max(vals)*.015,f'{v:g}',ha='center',fontsize=8)
    a.set_xticks(list(x),[r[0].replace('\n',' ') for r in cb],fontsize=8,rotation=45,ha='right')
    a.set_title(['M4–M5: Cinebench 2024 single-core','M4–M5: Cinebench 2024 multi-core'][k]+'\n(points / W, whole system)',fontsize=10)
from matplotlib.patches import Patch
fig.legend([Patch(color=c) for c in C.values()],['base','Pro','Max'],loc='upper right',frameon=False,ncol=3)
fig.suptitle('Apple Silicon Mac CPU efficiency (Notebookcheck, measured at the wall, external monitor)',x=.01,ha='left',fontsize=12,weight='bold')
fig.text(.01,.005,'Panels use different benchmarks: compare within a panel, not across. M2 Pro, base M3 and M1/M2 Max Cinebench 2024 efficiency not measured. M3 Pro 11c value attributed from an unlabeled comparison entry.',fontsize=8,color='#555')
fig.tight_layout(rect=(0,.03,1,.93)); fig.savefig('apple_silicon_efficiency.png',dpi=150)
