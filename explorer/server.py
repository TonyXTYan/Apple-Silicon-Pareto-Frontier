"""-> data17.json  Server-class CPUs, from server_rows.json (each row with the URL that was read; id = position in that list):
SPECpower_ssj2008 official results as a server-only entry of the CPU all-cores Benchmark menu (x = ssj_ops at 100% target
load in thousands, p = average AC wall power at 100%); HPL from Jeff Geerling's top500-benchmark runs on Ampere machines (average
wall power) and from CPU-only TOP500/Green500 systems (per-node shares of system-level power, graded weaker and drawn hollow);
Geerling's AmpereOne DeepSeek R1 671B run (average wall power); and Blender Open Data CPU medians whose power is borrowed from
the same chip and socket count's SPECpower 100%-load wall power (est+pe). Every row carries `srv`, which keeps it out of the
matrix and the All workloads view. Ampere is a comparison vendor of its own; EPYC sits under AMD, Xeon under Intel, Grace under
NVIDIA. Rows left out (no defensible power, or no vendor tier on the page) are listed in SKIP with the reason."""
import json, math
D=json.load(open('data16.json')); X={r['id']:r for r in json.load(open('server_rows.json'))['rows']}
url2key={v['url']:k for k,v in D['sources'].items()}
def src(u,name):
    if u not in url2key:
        k='srv_'+str(len([k for k in D['sources'] if k.startswith('srv_')])); D['sources'][k]=dict(name=name,url=u); url2key[u]=k
    return url2key[u]
VENDOR={'AMD':'AMD','Intel':'Intel','NVIDIA':'NVIDIA','Ampere':'Ampere'}
def chipname(r):
    c=r['chip']
    if c=='Altra M128-30': c='Altra Max M128-30'   # 128 cores at 3.0 GHz is the Altra Max M128-30 (Altra tops out at 80 cores)
    if c.startswith('AmpereOne A192-26X'): c='AmpereOne A192-32X'   # the A192-32X capped at 2.6 GHz, not a real 26X
    return VENDOR[r['vendor']]+' '+c
SL=lambda c:c.split(' ',1)[1].replace('Xeon Platinum ','').replace('Xeon CPU Max ','Xeon Max ').replace('Grace CPU Superchip','Grace').replace('Core Ultra 7 ','').replace('AmpereOne ','').replace('Altra Max ','').replace('Altra ','')
rows=[]; est=[]
def base(r,w,dev,sd,form,x,bench,note,q,srcname=None):
    c=chipname(r)
    return dict(w=w,chip=c,dev=dev,tier=r['vendor'],form=form,x=x,src=src(r['url'],srcname or r['src_name']),q=q,bench=bench,resc=False,note=note,sl=SL(c),sd=sd,srv=1)

# ---- SPECpower_ssj2008: a server-only entry in the CPU all-cores Benchmark menu
SPEC='SPECpower_ssj2008'
SPECDEV={0:('Dell PowerEdge R9815','R9815'),1:('Supermicro AS-2127H7-N','AS-2127H7'),2:('xFusion FusionServer 2158H V8','2158H V8'),3:('Asus RS720A-E13-RS8U','RS720A'),
  4:('Lenovo ThinkSystem SR655 V3','SR655 V3'),5:('Quanta S44NL-1U','S44NL'),6:('Lenovo ThinkSystem SR635 V3','SR635 V3'),7:('Lenovo ThinkSystem SR655 V3','SR655 V3'),
  8:('Lenovo ThinkSystem SR655 V3','SR655 V3'),9:('Lenovo ThinkEdge SE455','SE455'),10:('Supermicro AS-3015A-i','AS-3015A'),11:('Lenovo ThinkSystem ST45 V3','ST45 V3'),
  12:('Supermicro SYS-212HA-TN','SYS-212HA'),13:('Dell PowerEdge R770AP','R770AP'),14:('Dell PowerEdge R570','R570'),15:('Lenovo ThinkSystem SR650 V4','SR650 V4'),
  16:('Dell PowerEdge R470','R470'),17:('Supermicro SYS-212HA-TN','SYS-212HA'),18:('Supermicro SYS-521E-WR','SYS-521E'),19:('xFusion FusionServer 2288H V7','2288H V7'),
  20:('Supermicro SYS-521E-WR','SYS-521E'),21:('Supermicro ARS-221GL-NR','ARS-221GL'),22:('Gigabyte R152-P31','R152-P31'),23:('Foxconn (FII) Mt. Collins','Mt. Collins'),
  24:('FALINUX AnyStor-700EC-NM','AnyStor'),25:('Lenovo ThinkEdge SE100 (edge server)','SE100')}
EXTRA={0:'The EPYC 9996 is new in November 2026 and its generation is not stated on the disclosure; the name is taken as given.',
  17:'The Xeon 6990E+ (288 E-cores) is taken as named in the disclosure; its generation name was not confirmed.',
  21:'Grace sits in a GPU-ready 1U chassis with two 1,800 W supplies, which is why active idle is 298 W, 48% of full load: this point understates the chip.',
  25:'An edge server built on a laptop chip, the one bridge from these servers to the laptop-class chips on the rest of the page.',
  11:'Assigned to the EPYC 4005 series from AMD\'s naming only.'}
SPECN=('SPECpower_ssj2008 is a Java server-transaction workload (integer, cache and memory heavy, no vector floating point), so it is not a proxy for Cinebench. '
  'Power is the average AC input of the whole server at 100% target load, measured by a SPEC-accepted power analyser (power-supply losses, fans, BMC, disks and network cards included); '
  'submissions are vendor-tuned (BIOS, JVM, often one DIMM per channel and one power supply), so deployed servers draw more. ')
for i in range(26):
    r=X[i]; dev,sd=SPECDEV[i]; so=r['sockets']
    if so>1: dev+=f' ({so} sockets)'; sd+=' 2P'
    x=round(r['x']/1000,1); P=r['p_wall_w']
    note=(f"{r['x']:,.0f} ssj_ops at 100% load at {P:g} W, {r['ops_per_w_100']:,} ssj_ops per watt (shown here in thousands). "
          f"SPEC's official metric, which averages ten load levels and active idle, is {r['overall_ssj_ops_per_w']:,.0f} overall ssj_ops per watt; active idle {r['idle_w']:g} W ({r['idle_share_of_100pct']*100:.0f}% of full-load power). "
          f"{so} socket{'s' if so>1 else ''}, {r['cores']} cores, {r['memory_gb']:g} GB. "+SPECN+('Two sockets double both speed and power, so the efficiency barely changes. ' if so>1 else '')+EXTRA.get(i,''))
    o=base(r,'cpu-all',dev,sd,'server',x,f"SPECpower_ssj2008, 100% target load ({so}P, {r['cores']} cores)",note.strip(),'A',srcname=r['src_name'].replace('SPEC, ','SPEC ')+', '+r['url'].rsplit('-',1)[1].replace('.html',''))
    o.update(bm=SPEC,e=round(x/P,4),p=P)
    rows.append(o)
spec={(chipname(X[i]),X[i]['sockets']):rows[i] for i in range(26)}

# ---- HPL: Jeff Geerling's runs on Ampere machines (average wall power over the run, the same harness as the page's other HPL rows)
GEER_HPL='Jeff Geerling records average wall power over the run (Kill-A-Watt before 2024, a ThirdReality smart outlet since), the same harness and method as the page\'s other HPL rows; HPL runs on the CPU only. '
for i,dev,sd,q,extra in ((38,'Supermicro AmpereOne server (512 GB DDR5)','Supermicro','A','Run with the NVMe drives and 25G networking unplugged; with them connected, 2,996 Gflops at 725 W (4.13 Gflops/W). Idle is about 196 to 233 W.'),
                         (39,'Supermicro AmpereOne server, cores capped at 2.6 GHz','Supermicro 2.6 GHz','A','Not a real A192-26X: the A192-32X with every core capped at 2.6 GHz to stand in for it, in the same chassis.'),
                         (40,'System76 Thelio Astra','Thelio Astra','A','Ampere-optimised BLIS. A workstation tower; Geerling gives 415 to 440 W as total system draw (default OpenBLAS: 1,147.2 Gflops at 415 W).'),
                         (41,'Ampere Altra Developer Platform','Dev Platform','A','Wattage from the README table (Kill-A-Watt era). Geerling notes memory bandwidth limits this board.'),
                         (42,'Ampere Altra Dev Kit','Dev Kit','A','Numbers from the README results table.'),
                         (43,'Supermicro Ampere Altra server (early run)','Supermicro early','B','Weaker: an early, less-tuned run in a 2U server (README table), well below the tuned runs on the same chip; the source names the chip "Altra M128-30", which with 128 cores at 3.0 GHz is the Altra Max M128-30.')):
    r=X[i]; P=r['p_wall_w']; o=base(r,'hpl',dev,sd,r['form'],r['x'],'HPL 2.3 (CPU), Geerling top500-benchmark',GEER_HPL+extra,q,srcname='Jeff Geerling, top500-benchmark, issue #'+r['url'].rsplit('/',1)[1])
    o.update(e=round(r['x']/P,4),p=P); rows.append(o)
# ---- HPL: CPU-only TOP500/Green500 systems, per-node shares of system-level power
G5N=('System-level power, not a chip or single-node wall reading: x and power are the TOP500/Green500 system totals divided by a node count derived here (cores / cores per node, assuming two sockets per node), '
     'so the power is each node\'s share of the whole submission (nodes plus their share of interconnect and whatever else the measurement boundary covers; facility cooling is not counted, and most of these racks are direct-liquid-cooled, so node fans are absent). '
     'These are thousand-node runs with vendor-tuned HPL (AOCL or MKL), and Level 1 measurements extrapolate from a subset of nodes. Read them as an indirect, upper bound on what one of these chips does at the wall, not as a measurement like the Geerling rows. ')
G5DEV={26:('Teton (HPE Cray EX), per node','Teton node'),27:('Roihu-C (BullSequana XH3000), per node','Roihu-C node'),28:('Cirrus (HPE Cray EX), per node','Cirrus node'),
       29:('PITAGORA CPU (Lenovo SD665 V3), per node','Pitagora node'),30:('Athena (HPE Cray EX), per node','Athena node'),31:('ASPIRE 2B CPU partition (HPE Cray EX4252 Gen 2), per node','Aspire 2B node'),
       32:('Carpenter (HPE Cray EX), per node','Carpenter node'),33:('CRESCO8 (Lenovo SD650 V3), per node','Cresco8 node'),34:('Genkai Node Group A (Fujitsu PRIMERGY CX2550 M7), per node','Genkai node'),
       35:('MareNostrum 5 GPP (Lenovo SD650 V3), per node','MN5 GPP node'),36:('Camphor 3 (Dell PowerEdge C6620), per node','Camphor 3 node')}
for i,(dev,sd) in G5DEV.items():
    r=X[i]; P=r['p_wall_w']; lvl=r['power_measurement_level']
    site=r['device'].split('(',1)[1].rsplit(')',1)[0]
    note=(G5N+f"System: {site}; Rmax {r['system_rmax_pflops']:g} PFlop/s at {r['system_power_kw']:,.1f} kW, {r['green500_gflops_per_w']:g} GFlops/W on the Green500 list (November 2026); "
          f"power measurement level {lvl if lvl[0].isdigit() else 'not stated'}; {r['nodes_derived']:,} nodes derived, {r['sockets']} sockets and {r['cores']} cores per node. If the node count is wrong, x and power scale together and the efficiency is unchanged.")
    o=base(r,'hpl',dev,sd,'server',r['x'],'HPL, TOP500/Green500 submission, per-node share of system power',note,'B',srcname='TOP500/Green500 November 2026, system '+r['url'].rstrip('/').rsplit('/',1)[1])
    o.update(e=round(r['x']/P,4),p=P,sys=1); rows.append(o)
# ---- LLM: AmpereOne DeepSeek R1 671B with average wall power
r=X[45]; o=base(r,'llm','Supermicro AmpereOne server (512 GB DDR5)','Supermicro','server',r['x'],'Ollama (CPU only), deepseek-r1:671b, eval rate',
   'Ollama on the 192 CPU cores, no GPU. The issue text gives 4.18 tokens per second "using on average 477W from the wall", an average rather than the peak used for Geerling\'s other LLM rows (his README column is labelled Power (Peak)), so it is not a lower bound like them. '
   'Weaker: the quantisation is not stated (Ollama\'s default 671b tag). On the same table the M3 Ultra Mac Studio runs this model at 19.89 tokens per second at 261.8 W peak. The three other AmpereOne models in his README (Llama 3.2 3B, Llama 3.1 70B and 405B) have no power and are left out.',
   'B',srcname='Jeff Geerling, ai-benchmarks, issue #10')
o.update(model='DeepSeek R1 671B',e=round(r['x']/r['p_wall_w'],4),p=r['p_wall_w']); rows.append(o)
# ---- Blender Open Data CPU medians: power borrowed from the same chip and socket count's SPECpower 100%-load wall power
FLO,FHI=1.0,1.3; FC=math.sqrt(FLO*FHI); SF=math.log(FHI/FLO)/2; SCH=0.10   # Blender draws more than SSJ at 100% (vector-heavy); extra spread for a different chassis
sxn=lambda n:0.04+0.15/math.sqrt(n)
BLN=('Render speed measured (Blender Open Data median over every machine with this CPU and socket count under Linux); no power is in Open Data. Wall power is estimated as 1.0 to 1.3 times (central {fc:.2f}) the SPECpower_ssj2008 100%-load wall power of the {dev} with this chip ({p:g} W): '
     'Cycles keeps every vector unit busy and usually draws more than the Java transactions of SPECpower, and 10% more spread is allowed because the Open Data machines are not the SPEC chassis (whose vendor-tuned configuration draws less than a typical deployment). ')
for i in (49,50,52,56,57,59,61):
    r=X[i]; c=chipname(r); so=r['sockets']; b=spec[(c,so)]; n=int(r['bench'].split(' over ')[1].split(' run')[0]); x=r['x']
    P=FC*b['p']; sP=math.sqrt(SF*SF+SCH*SCH); sx=sxn(n); s=math.sqrt(sP*sP+sx*sx); e=x/P
    note=BLN.format(fc=FC,dev=b['dev'],p=b['p'])+f"{n} run{'s' if n>1 else ''}"+(' (weaker: three or fewer)' if n<=3 else '')+'. '+r['notes'].split('. Speed only')[0].split('Sum of three scenes per run; median of runs. ')[1]+'.'
    o=base(r,'bl-cpu',b['dev']+' (estimate)',b['sd'],'server',round(x,3),r['bench'],note,'B' if n<=3 else 'E',srcname='Blender Open Data snapshot (Blender 4.5.0), Linux medians by socket count')
    o.update(ck=c,gen=0,xlo=round(x*math.exp(-sx),3),xhi=round(x*math.exp(sx),3),e=round(e,4),elo=round(e*math.exp(-s),4),ehi=round(e*math.exp(s),4),
             p=round(P,1),plo=round(P*math.exp(-sP),1),phi=round(P*math.exp(sP),1),est=1,pe=1,seen=True,psrc=b['src'])
    est.append(o)
SKIP={37:'Fugaku A64FX: Fujitsu has no vendor tier on the page (optional extra in the research)',44:'Grace LINPACK from the BSC/SUNY study: no power',
      46:'AmpereOne Llama 3.2 3B: no power',47:'AmpereOne Llama 3.1 70B: no power',48:'AmpereOne Llama 3.1 405B: no power',
      51:'EPYC 9755 2P Blender: SPECpower has only a 1P result',53:'EPYC 9745 2P Blender: no SPECpower result',54:'EPYC 9655 2P Blender: SPECpower has only a 1P result',
      55:'EPYC 9655P Blender: SPECpower has the 9655, a different SKU',58:'EPYC 4585PX Blender: no SPECpower result',60:'EPYC 4545P Blender: no SPECpower result',
      62:'Xeon 6972P Blender: no SPECpower result',63:'Xeon 6960P Blender: no SPECpower result',64:'Xeon 6740E Blender: no SPECpower result (the 6780E is a different SKU)',
      65:'Xeon Platinum 8468 Blender: no SPECpower result',66:'Threadripper PRO 9995WX: a workstation with no wall power',67:'Threadripper PRO 7995WX: no wall power',
      68:'Threadripper 9980X: no wall power',69:'Threadripper 7980X: no wall power',70:'Xeon w9-3495X: no wall power'}
used=set(range(26))|{38,39,40,41,42,43,45,49,50,52,56,57,59,61}|set(G5DEV)
assert used|set(SKIP)==set(X) and not used&set(SKIP)
D['rows']+=rows; D['est']+=est
json.dump(D,open('data17.json','w'),separators=(',',':'))
from collections import Counter
for o in rows+est: print(f"{o['w']:7} {o.get('bm',''):17} {o['chip'][:30]:30} {o['dev'][:46]:46} x={o['x']:<10} p={o['p']:<7} e={o['e']:<8} q={o['q']} {'sys' if o.get('sys') else ''}{'pe' if o.get('pe') else ''}")
print(dict(Counter(o['w'] for o in rows+est)),'skipped',len(SKIP))
