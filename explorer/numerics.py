"""-> data9.json  Numerical libraries: single-precision GEMM with Accelerate and OpenBLAS (Julia Discourse thread, 10 chips,
2048^3), Accelerate on the CPU against Metal MPS on the GPU (Hubner et al., arXiv 2502.05317, M1 to M4 base chips), and fp64
DGEMM on the performance cores (Julia Discourse). Speeds are single community or paper runs; no wall power was metered, so
power is 0.5 to 1.4 times the Cinebench all-core wall power of the same chip on this page."""
import json, math
D=json.load(open('data8.json'))
TIER=lambda c:'Ultra' if 'Ultra' in c else 'Max' if 'Max' in c else 'Pro' if 'Pro' in c else 'base'
ck=lambda c:c.rsplit(' ',1)[0] if c.endswith('c') and c.split()[-1][:-1].isdigit() else c
FLO,FHI=0.5,1.4; F=math.sqrt(FLO*FHI); SF=math.log(FHI/FLO)/2   # factor on Cinebench wall power, log-centred
SX=0.05   # one run each: 5% allowed for run-to-run spread
ca=[r for r in D['rows'] if r['w']=='cpu-all' and not r.get('ex')]
ce={r['chip']:r for r in D['est'] if r['w']=='cpu-all' and not r.get('mode')}
def cinebench(chip,dev=None):
    """The Cinebench all-core row whose power is borrowed: the named machine, else the chip's best-measured machine
    (Cinebench 2024 before R23-converted rows, then the narrowest wall-power range), else the model estimate."""
    m=[r for r in ca if ck(r['chip'])==chip]
    if dev: m=[r for r in m if r['dev']==dev]
    if m:
        r=min(m,key=lambda r:(r['resc'],r['phi']/r['plo'])); return r,math.log(r['phi']/r['plo'])/2,'Notebookcheck'
    r=ce[chip]; return r,math.log(r['ehi']/r['elo'])/2,'model estimate'
SRC={'jl':('julia_gemm','Julia Discourse, AppleNeuralEngine.jl thread (GEMM with Accelerate and OpenBLAS); power estimated on this page','https://discourse.julialang.org/t/-/140344'),
     'ax':('arxiv_2502','Hubner et al., Apple vs. Oranges (arXiv 2502.05317), SGEMM on M1 to M4; power estimated on this page','https://arxiv.org/html/2502.05317v1'),
     'dg':('julia_dgemm','Julia Discourse, memory-bound performance on M3 Ultra and M4 Max (DGEMM); power estimated on this page','https://discourse.julialang.org/t/a-brief-study-of-memory-bound-application-performance-on-m3-ultra-and-m4-max-in-julia/128459')}
rows=[]
def add(chip,setk,lib,x,src,bench,speed,dev=None,ord_=None,grp=True,extra=''):
    r0,sP,how=cinebench(chip,dev); P=F*r0['p']; sp=math.sqrt(sP*sP+SF*SF); s=math.sqrt(sp*sp+SX*SX); e=x/P
    mach=r0['dev'].replace(' (estimate)','')
    note=(speed+' No wall power was metered for any of these runs. Power is estimated as 0.5 to 1.4 times (central 0.84) the Cinebench 2024 all-core wall power of the '
          +f"{r0['chip']} {mach} ({r0['p']:g} W, {how})"+('' if dev else ', the best-measured machine with this chip, because the source does not name the machine')+'. '
          'GEMM through Accelerate runs on the matrix units and stops scaling after about two threads, so it can draw less than an all-core render; '
          'HPL, a sustained double-precision run, draws 1.1 to 1.4 times the Cinebench power on the machines that have both (M4 Mac mini 39.6 against 35.2 W, M1 Max Mac Studio 66 against 46.6 W).'+(' '+extra if extra else ''))
    r=dict(w='blas',set=setk,lib=lib,chip=chip,ck=chip,gen=int(chip[1]),dev=mach+('' if dev else ' (estimate)'),tier=TIER(chip),form=r0['form'],
           x=x,xlo=round(x*math.exp(-SX),2),xhi=round(x*math.exp(SX),2),e=round(e,3),elo=round(e*math.exp(-s),3),ehi=round(e*math.exp(s),3),
           p=round(P,1),plo=round(P*math.exp(-sp),1),phi=round(P*math.exp(sp),1),q='E',est=1,pe=1,seen=True,src=SRC[src][0],resc=False,bench=bench,note=note)
    if grp: r.update(grp=chip+'|'+setk,ord=ord_)
    rows.append(r)
# ---- A: Julia, fp32 GEMM 2048 x 2048 x 2048, Accelerate and OpenBLAS (chip: Accelerate, OpenBLAS, BLAS threads, Julia, macOS)
JL=[('M1 Pro',1858,504,6,'1.13.1','27.0.1'),('M1 Max',1876,719,8,'1.12.7','26.6.2'),('M2 Pro',2214,553,6,'1.13.2','27.0.1'),('M2 Max',2378,714,8,'1.13.3','27.0.1'),
    ('M3 Max',3047,1177,12,'1.13.3','26.7.2'),('M3 Ultra',5097,1799,20,'1.12.6','26.6.2'),('M4',1861,384,4,'1.13.3','27.0.1'),('M4 Pro',3406,790,8,'1.13.3','26.5.1'),
    ('M5 Pro',2773,1431,17,'1.13.3','27.0.1'),('M5 Max',2772,1426,17,'1.13.3','27.2')]
for c,acc,ob,th,jv,mv in JL:
    for lib,x,o in (('OpenBLAS',ob,0),('Accelerate',acc,1)):
        add(c,'julia-sgemm',lib,x,'jl',f'Julia {jv}, single-precision GEMM 2048 x 2048 x 2048 via {lib}, {th} BLAS threads, macOS {mv}',
            f'Speed measured: one community run in the Julia Discourse AppleNeuralEngine.jl thread (late October 2026), {lib} {x:,} GFLOPS against {acc if lib=="OpenBLAS" else ob:,} with {"Accelerate" if lib=="OpenBLAS" else "OpenBLAS"} on the same machine ({acc/ob:.2f} times).',ord_=o)
# ---- B: Hubner et al., peak SGEMM, Accelerate on the CPU and MPS on the GPU (chip, machine on this page, Accelerate, MPS, CPU and GPU TFLOPS/W from powermetrics)
AX=[('M1','MacBook Air 13',900,1360,0.25,0.21,'MacBook Air (2020, 8 GB)'),('M2','Mac mini',1090,2240,0.2,0.4,'Mac mini (2023, 16 GB)'),
    ('M3','MacBook Air 13',1380,2470,0.27,0.46,'MacBook Air (2024, 8 GB)'),('M4','Mac mini',1490,2900,0.23,0.33,'Mac mini (2024, 16 GB)')]
for c,dev,acc,mps,tc,tg,mach in AX:
    for lib,x,o,t in (('Accelerate (CPU)',acc,0,tc),('MPS (GPU)',mps,1,tg)):
        add(c,'arxiv-sgemm',lib,x,'ax',f'Peak single-precision GEMM via {"Accelerate on the CPU" if o==0 else "Metal Performance Shaders on the GPU"}, {mach}',
            f'Speed measured by Hubner et al. (arXiv 2502.05317, January 2025 hardware) on a {mach}: peak {x/1000:g} TFLOPS. The paper reports {t:g} TFLOPS per watt from powermetrics {"CPU" if o==0 else "GPU"} package power ({t*1000:g} GFLOP per joule), which leaves out the rest of the machine, so wall efficiency must be lower.',
            dev=dev,ord_=o,extra='The same CPU-load wall power is used for the GPU point, since no GPU-only wall reading exists for these machines.' if o else '')
# ---- D: Julia, fp64 DGEMM N=8192 on the performance cores (chip, GFLOPS, P-cores, theoretical peak, machine on this page or None)
DG=[('M1',181,4,205,None),('M4 Max',698,12,747,None),('M3 Ultra',1073,20,1145,None)]
for c,x,pc,pk,dev in DG:
    add(c,'julia-dgemm','DGEMM fp64',x,'dg',f'Julia, double-precision GEMM N = 8192 on {pc} performance cores (BLAS not stated)',
        f'Speed measured: one community run in the Julia Discourse thread on M3 Ultra and M4 Max memory-bound performance, {x:,} GFLOPS against a theoretical {pk:,} for the performance cores.',grp=False)
D['est']+=rows
for k,n,u in SRC.values(): D['sources'][k]=dict(name=n,url=u)
json.dump(D,open('data9.json','w'),separators=(',',':'))
for r in rows: print(f"{r['set']:12} {r['lib']:17} {r['chip']:9} {r['dev']:28} x={r['x']:6} P={r['p']:6} [{r['plo']},{r['phi']}] e={r['e']} [{r['elo']},{r['ehi']}]")
