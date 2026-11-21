import numpy as np, matplotlib.pyplot as plt, csv
from matplotlib.lines import Line2D
from adjustText import adjust_text
import matplotlib.patheffects as pe

# (chip, device, tier, form, bench, S_multi, (S_lo,S_hi)|None, P_multi(avg,lo,hi), S_single, P_single(avg,lo,hi))
# power: avg, P1 (min where no P1 published), max  -- whole system at the wall, external monitor
L,F,D='laptop','fanless','desktop'
rows=[
# --- Cinebench R23 era (Notebookcheck M2 Pro/Max, M3, M3 Pro/Max analyses; Mac mini / Mac Studio reviews)
('M1','Air 13','base',F,'R23',7409,(6401,7409),(22,18.8,25.2),1496,(9.06,8.57,19)),
('M2','Air 13 8c-GPU','base',F,'R23',8667,None,(25.3,23.5,27.5),1585,(8.84,8.37,9.82)),
('M2','Air 13 10c-GPU','base',F,'R23',8517,None,(24.9,22.3,29.1),1580,(9.13,8.74,10.1)),
('M2','MBP13','base',L,'R23',8745,None,(25.3,24.5,27.2),1581,(9.78,9.21,11.2)),
('M1 Pro','MBP16','Pro',L,'R23',12370,None,(42.7,25.7,50.1),1534,(13.9,13.3,22.1)),
('M2 Pro 10c','MBP14','Pro',L,'R23',11811,None,(47.2,46.1,48.5),1643,(13.9,12.7,16.5)),
('M2 Pro 12c','MBP14','Pro',L,'R23',14787,None,(53.7,51.2,60.8),1647,(11.7,10.7,13.6)),
('M2 Max','MBP16','Max',L,'R23',14767,None,(63.5,62.1,67.8),1625,(22.6,18.2,29.7)),
('M3','MBP14','base',L,'R23',10454,None,(27.9,27,30),1904,(10.0,9.57,12.8)),
('M3 Pro 11c','MBP14','Pro',L,'R23',13315,None,(33.8,33.1,36.3),1942,(9.78,9.0,10.8)),
('M3 Pro 12c','MBP16','Pro',L,'R23',15106,None,(42.2,41.5,43.6),1977,(13.9,12.2,15.8)),
('M3 Max','MBP14','Max',L,'R23',24020,None,(78.3,76.1,81.7),1950,(15.5,13.6,22.6)),
('M3 Max','MBP16','Max',L,'R23',24024,None,(78.6,73.3,80.2),1968,(17.3,16.2,21.4)),
('M1 Max','Studio','Max',D,'R23',12396,None,(46.6,45.6,48.5),1536,(18.9,17.9,19.9)),
('M2','mini','base',D,'R23',8772,None,(23.6,22.9,24.7),1638,(10.1,9.65,12.9)),
('M2 Max','Studio','Max',D,'R23',14738,None,(50.7,49,53.4),1662,(19.4,15.6,22.9)),
('M4 Pro 12c','mini','Pro',D,'R23',19844,None,(60.1,58.6,70.1),2254,(15.1,14.4,26.5)),
# --- Cinebench 2024 era (Notebookcheck M5, M5 Pro/Max, M6 analyses; Mac mini 2026 review)
('M3','Air 13','base',F,'CB24',601,None,(21.2,17.7,33),141,(11.1,10.4,14)),
('M4','Air 13','base',F,'CB24',815,None,(20.9,17.6,30.7),173,(13.3,12.5,15.5)),
('M4','Air 15','base',F,'CB24',874,None,(25.9,22.5,37.2),173,(12.8,11.7,15.3)),
('M4','MBP14','base',L,'CB24',986,None,(39.8,36.5,42.4),174,(12.8,11.5,14.4)),
('M4 Pro 12c','MBP14','Pro',L,'CB24',1435,(1403,1435),(65.7,60.2,73.1),176,(18.4,16.8,36.7)),
('M4 Pro 14c','MBP14','Pro',L,'CB24',1662,None,(73.6,68.7,87.4),177,(16,13.8,18.4)),
('M4 Pro 14c','MBP16','Pro',L,'CB24',1729,None,(85.8,77.7,89.6),178,(18.7,17.5,20.5)),
('M4 Max','MBP16','Max',L,'CB24',2069,(2015,2069),(92.2,87.1,105.4),178,(21.6,20.1,23.2)),
('M5','MBP14','base',L,'CB24',1172,None,(42.6,39.6,52.8),200,(15.3,14.4,18.8)),
('M5','Air 15','base',F,'CB24',962,None,(27.6,25.1,37),199,(15.6,14.6,20.2)),
('M5 Pro','MBP16','Pro',L,'CB24',2347,None,(102,87,123.5),201,(21,20,23.3)),
('M5 Max','MBP14','Max',L,'CB24',2073,None,(84.1,66,96.5),200,(21.9,20.4,26.5)),
('M5 Max','MBP16','Max',L,'CB24',2437,None,(117.5,108.8,129.6),201,(21.5,18.9,25.1)),
('M4','mini','base',D,'CB24',958,None,(35.2,31.5,36.5),177,(12.6,11,19.6)),
('M6','mini','base',D,'CB24',1468,None,(45.2,42.2,47.2),221,(14.5,13.8,17.6)),
]
# Anchor: M4 Mac mini, measured in BOTH benchmarks on the same unit
A={'R23':dict(Sm=13845,Pm=33.1,Ss=2269,Ps=12.2),'CB24':dict(Sm=958,Pm=35.2,Ss=177,Ps=12.6)}
kS={'m':A['R23']['Sm']/A['CB24']['Sm'],'s':A['R23']['Ss']/A['CB24']['Ss']}          # R23 pts per CB24 pt
kE={'m':(A['R23']['Sm']/A['R23']['Pm'])/(A['CB24']['Sm']/A['CB24']['Pm']),
    's':(A['R23']['Ss']/A['R23']['Ps'])/(A['CB24']['Ss']/A['CB24']['Ps'])}          # R23 pts/W per CB24 pt/W
print('score scale multi %.2f single %.2f | eff scale multi %.2f single %.2f'%(kS['m'],kS['s'],kE['m'],kE['s']))
# Stitch residuals: devices with a native CB24 score AND an R23 score
chk=[('M3 MBP14',10454,712,1904,140),('M3 Pro 11c',13315,908,1942,144),('M3 Pro 12c',15106,1059,1977,143),
     ('M3 Max MBP14',24020,1532,1950,140),('M4 Pro mini',19844,1455,2254,174)]
rm=[np.log(r/kS['m']/c) for _,r,c,_,_ in chk]; rs=[np.log(r/kS['s']/c) for *_,r,c in chk]
sig={'m':float(np.sqrt(np.mean(np.square(rm)))),'s':float(np.sqrt(np.mean(np.square(rs))))}
print('stitch residuals multi',np.round(np.exp(rm),3),'rms %.3f'%sig['m']); print('single',np.round(np.exp(rs),3),'rms %.3f'%sig['s'])

ref=A['CB24']['Sm']/A['CB24']['Pm']   # 27.2 pts/W = 1.0
pts=[]
for chip,dev,tier,form,b,Sm,Sr,Pm,Ss,Ps in rows:
    for job,S,Srng,P in (('m',Sm,Sr,Pm),('s',Ss,None,Ps)):
        x=S/(kS[job] if b=='R23' else 1); eff=S/P[0]/(kE[job] if b=='R23' else 1)/ref
        lo=eff*P[0]/P[2]; hi=eff*P[0]/P[1]                       # power range -> efficiency range
        xlo,xhi=(x*Srng[0]/S,x*Srng[1]/S) if Srng else (x,x)
        if b=='R23':                                              # add stitch uncertainty in quadrature (log space)
            s=sig[job]
            lo=eff*np.exp(-np.hypot(np.log(eff/lo),s)); hi=eff*np.exp(np.hypot(np.log(hi/eff),s))
            xlo=x*np.exp(-np.hypot(np.log(x/xlo),s)); xhi=x*np.exp(np.hypot(np.log(xhi/x),s))
        pts.append(dict(chip=chip,dev=dev,tier=tier,form=form,b=b,job=job,x=x,y=eff,lo=lo,hi=hi,xlo=xlo,xhi=xhi,P=P[0],S=S))
with open('apple_silicon_efficiency_data.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['chip','device','tier','form','benchmark','job','raw_score','wall_power_W','throughput_CB24eq_pts','work_per_joule_rel_M4mini','wpj_lo','wpj_hi'])
    for p in pts: w.writerow([p['chip'],p['dev'],p['tier'],p['form'],p['b'],'all-core' if p['job']=='m' else 'single-thread',p['S'],p['P'],round(p['x'],1),round(p['y'],3),round(p['lo'],3),round(p['hi'],3)])

SURF='#fcfcfb'; INK='#0b0b0b'; INK2='#52514e'; GRID='#e4e3df'
COL={'base':'#2a78d6','Pro':'#eb6834','Max':'#1baf7a'}; MK={L:'o',F:'^',D:'s'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.edgecolor':'#b9b8b2','text.color':INK,'axes.labelcolor':INK2,'xtick.color':INK2,'ytick.color':INK2})
fig,ax=plt.subplots(figsize=(19,11.5),facecolor=SURF); ax.set_facecolor(SURF)
ax.set_xscale('log'); ax.set_yscale('log')
X0,X1,Y0,Y1=98,3000,0.158,1.72
xx=np.array([X0,X1])
for P in (10,20,40,80,160):
    yy=xx/P/ref; ax.plot(xx,yy,color='#cfcec8',lw=.8,ls=(0,(4,4)),zorder=1)
    xl=min(X1*.93, Y1*.955*P*ref); ax.text(xl,xl/P/ref*1.02,f'{P} W',fontsize=8,color='#8a8983',rotation=38,ha='right',va='bottom',zorder=1)
TO={'base':0,'Pro':1,'Max':2}; FO={F:0,L:1,D:2}
def key(p): return (int(p['chip'][1]),TO[p['tier']],p['chip'],FO[p['form']],p['dev'])
ids={}
for p in sorted(pts,key=key):
    ids.setdefault((p['chip'],p['dev']),len(ids)+1)
NAMED={('M4','Air 13'):'M4 Air 13',('M6','mini'):'M6 mini',('M5 Max','MBP16'):'M5 Max MBP16',('M2 Max','MBP16'):'M2 Max MBP16',('M1','Air 13'):'M1 Air 13',('M4','mini'):'M4 mini = 1×'}
texts=[]
for p in pts:
    c=COL[p['tier']]; filled=p['b']=='CB24'; n=ids[(p['chip'],p['dev'])]
    ax.errorbar(p['x'],p['y'],yerr=[[p['y']-p['lo']],[p['hi']-p['y']]],xerr=[[p['x']-p['xlo']],[p['xhi']-p['x']]],
                fmt='none',ecolor=c,elinewidth=1.0,alpha=.5,capsize=2,capthick=.8,zorder=2)
    ax.plot(p['x'],p['y'],MK[p['form']],ms=9.5,mfc=c if filled else SURF,mec=SURF if filled else c,mew=1.2 if filled else 1.8,zorder=3)
    lab=str(n)+('  '+NAMED[(p['chip'],p['dev'])] if p['job']=='m' and (p['chip'],p['dev']) in NAMED else '')
    texts.append(ax.text(p['x']*1.012,p['y']*1.012,lab,fontsize=8.6,weight='bold',color=INK,zorder=5,
                 path_effects=[pe.withStroke(linewidth=2.2,foreground=SURF)]))
ax.set_xlim(X0,X1); ax.set_ylim(Y0,Y1)
adjust_text(texts,x=[p['x'] for p in pts],y=[p['y'] for p in pts],ax=ax,expand=(1.5,1.6),force_text=(.25,.35),force_static=(.5,.6),
            arrowprops=dict(arrowstyle='-',color='#8f8e88',lw=.5),min_arrow_len=14,iter_lim=1500)
def nudge(chip,dev,job,fx,fy,ha='left'):
    for p,t in zip(pts,texts):
        if (p['chip'],p['dev'],p['job'])==(chip,dev,job): t.set_position((p['x']*fx,p['y']*fy)); t.set_ha(ha); t.set_va('center')
nudge('M1','Air 13','s',.972,1.0,'right'); nudge('M3 Pro 11c','MBP14','m',.975,.965,'right'); nudge('M2','Air 13 10c-GPU','m',.975,1.03,'right')
nudge('M2','Air 13 8c-GPU','m',1.0,1.055,'center'); nudge('M3 Max','MBP14','m',.975,1.03,'right'); nudge('M3 Max','MBP16','m',.985,.955,'right')
ax.set_xticks([100,150,200,300,500,700,1000,1500,2000,3000]); ax.set_xticklabels(['100','150','200','300','500','700','1,000','1,500','2,000','3,000'])
yt=[.16,.2,.25,.3,.4,.5,.6,.8,1,1.2,1.5]; ax.set_yticks(yt); ax.set_yticklabels([f'{v:g}×' for v in yt]); ax.minorticks_off()
ax.grid(color=GRID,lw=.7,zorder=0); ax.spines[['top','right']].set_visible(False)
ax.axvspan(X0,262,color='#f1f0ec',zorder=0,lw=0)
ax.text(105,1.66,'ONE THREAD BUSY',fontsize=9,color=INK2,weight='bold',va='top'); ax.text(275,1.66,'ALL CORES BUSY',fontsize=9,color=INK2,weight='bold',va='top')
ax.set_xlabel('Throughput: rate of work done (Cinebench 2024 points, log scale)   →  faster',fontsize=10.5)
ax.set_ylabel('Work done per joule of wall energy (M4 Mac mini, all cores = 1×, log scale)   →  more efficient',fontsize=10.5)
h=[Line2D([],[],marker='o',ls='',ms=9,mfc=COL[t],mec=SURF,label=t if t!='base' else 'base chip') for t in COL]
h+=[Line2D([],[],marker=MK[k],ls='',ms=9,mfc='#77766f',mec=SURF,label=l) for k,l in ((L,'laptop with fan'),(F,'fanless laptop (Air)'),(D,'desktop (mini / Studio)'))]
h+=[Line2D([],[],marker='o',ls='',ms=9,mfc='#77766f',mec=SURF,label='measured in Cinebench 2024'),
    Line2D([],[],marker='o',ls='',ms=9,mfc=SURF,mec='#77766f',mew=1.8,label='Cinebench R23, rescaled via M4 mini'),
    Line2D([],[],color='#cfcec8',lw=.9,ls=(0,(4,4)),label='constant wall power')]
ax.legend(handles=h,loc='lower right',ncol=3,frameon=True,framealpha=1,facecolor=SURF,edgecolor='#dddcd6',fontsize=8.8,columnspacing=1.6,handletextpad=.5,borderpad=.9)
seen=set(); kh=[]; kl=[]; lastg=None
for p in sorted(pts,key=key):
    t=(p['chip'],p['dev'])
    if t in seen: continue
    seen.add(t); g=p['chip'][:2]
    if lastg and g!=lastg: kh.append(Line2D([],[],ls='',marker='')); kl.append('')
    lastg=g; filled=p['b']=='CB24'; c=COL[p['tier']]
    kh.append(Line2D([],[],ls='',marker=MK[p['form']],ms=7.5,mfc=c if filled else SURF,mec=SURF if filled else c,mew=1 if filled else 1.6))
    kl.append(f"{ids[t]:>2}  {p['chip']} · {p['dev'].replace('MBP','MacBook Pro ').replace('Air','MacBook Air').replace('mini','Mac mini').replace('Studio','Mac Studio')}")
kleg=fig.legend(kh,kl,loc='upper left',bbox_to_anchor=(.835,.918),frameon=False,fontsize=8.6,labelspacing=.42,handletextpad=.4,title='MACHINES',alignment='left')
kleg.get_title().set_fontsize(9); kleg.get_title().set_fontweight('bold'); kleg.get_title().set_color(INK2)
fig.text(.04,.968,'Apple Silicon Macs: computational work per joule vs. speed, M1 to M6',fontsize=15,weight='bold',ha='left')
fig.text(.04,.943,'Each machine appears twice: once running a single-thread job (left band) and once running an all-core job (right). Whole-system power at the wall, external monitor.',fontsize=10,color=INK2,ha='left')
fig.text(.04,.016,f"Source: Notebookcheck measurements. Work per joule = score ÷ average wall power. Error bars: range of instantaneous wall power during the run (1st percentile to max), plus score spread where several runs exist;\n"
         f"hollow points add the R23→2024 conversion uncertainty ({sig['m']*100:.0f}% all-core, {sig['s']*100:.0f}% single-thread, from 5 machines scored in both). 1× = 27.2 points per watt.",fontsize=8.3,color=INK2,ha='left',va='bottom',linespacing=1.5)
fig.subplots_adjust(left=.065,right=.825,top=.92,bottom=.105)
fig.savefig('apple_silicon_work_per_joule.png',dpi=150,facecolor=SURF)
