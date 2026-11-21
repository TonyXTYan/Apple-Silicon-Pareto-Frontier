"""-> data21.json  Per-scene Blender rows (monster, junkshop, classroom) for every comparison and server chip that had only a
three-scene point, on both devices (bl-cpu and bl-gpu), from blscenes_rows.json (id = position in that list). Each row there
holds the runs of the Blender Open Data snapshot that give the existing three-scene point, selected again with the same Blender
version, compute type, device name and filters: sum_spm is their median of per-run sums (it must reproduce the three-scene
point) and scenes_median_spm the median of each scene over the same runs. A median of sums is not the sum of medians, so the
three scene medians are scaled by sum_spm / (their sum), which the notes state; the scenes then add up to the three-scene point.
Each scene row copies the three-scene row's power, power range, speed and efficiency spread, est/pe/q flags, form, tier,
source and labels, as the Apple and Snapdragon scene rows do, and assumes each scene draws the same power as the three-scene
run. The three-scene rows and every Apple row are left unchanged. Machines that cannot get scene rows are listed in
`exceptions` of the rows file with the reason (none at present)."""
import json, math
D=json.load(open('data20.json')); J=json.load(open('blscenes_rows.json')); X={r['id']:r for r in J['rows']}
SCENES=('monster','junkshop','classroom')
sums=[r for r in D['rows']+D['est'] if r['w'] in ('bl-cpu','bl-gpu') and not r.get('scene')]
has=lambda t:any(r['w']==t['w'] and r['chip']==t['chip'] and r['dev']==t['dev'] and r.get('scene') for r in D['rows']+D['est'])
est=[]
for i in sorted(X):
    r=X[i]; t=[q for q in sums if q['w']==r['w'] and q['chip']==r['chip'] and q['dev']==r['dev']]
    assert len(t)==1, ('three-scene row not found once',r['chip'],r['dev']); t=t[0]
    assert not has(t), ('already has scene rows',r['chip'])
    assert abs(r['sum_spm']/60-t['x'])<=max(0.002,1e-4*t['x']), ('runs must reproduce the three-scene point',r['chip'],r['sum_spm']/60,t['x'])
    raw=[r['scenes_median_spm'][s] for s in SCENES]; k=r['sum_spm']/sum(raw); n=r['n']
    runs=f"{n} run{'s' if n>1 else ''}"
    od=f"the {r['device']}"+(f" ({r['filter']})" if r['filter'] else '')
    for s,m in zip(SCENES,raw):
        spm=m*k; x=spm/60
        scl=(f", scaled by {100*(k-1):+.1f}% to {spm:,.1f} so that the three scene medians add up to the three-scene point's median of per-run sums ({r['sum_spm']:,.2f})"
             if abs(k-1)>=0.0005 else '')
        cnt=(f" The snapshot has {n} complete runs under this device name, whose median of sums reproduces the three-scene point (that row's text gives {r['n_sum_row']})."
             if r.get('n_sum_row') else '')
        note=(f"Render speed measured (Blender Open Data, the {s} scene of the same {runs} of {od} under {r['system']}, Blender {r['blender']}, that give the three-scene point: "
              f"median {m:,.1f} samples/min{scl})."+cnt+" Power, its range and the speed spread are those of the three-scene point, and each scene is assumed to draw the same power as the three-scene run. "
              "Three-scene point: "+t['note'])
        o={kk:v for kk,v in t.items() if kk not in ('x','xlo','xhi','e','elo','ehi','bench','note','grp')}
        e=x/t['p']
        o.update(x=round(x,3),xlo=round(x*t['xlo']/t['x'],3),xhi=round(x*t['xhi']/t['x'],3),e=round(e,4),elo=round(e*t['elo']/t['e'],4),ehi=round(e*t['ehi']/t['e'],4),
                 bench=f"Blender {r['blender']} {r['backend']}, {s} scene, Open Data, {runs}, {spm:,.1f} samples/min" + (f" (scene median {m:,.1f}, scaled {100*(k-1):+.1f}%)" if scl else '') + f" (device \"{r['device']}\")",
                 note=note,scene=s)
        if t.get('grp'): o['grp']=t['grp']+'|'+s
        est.append(o)
    assert abs(sum(o['x'] for o in est[-3:])-t['x'])<=0.01*t['x']
D['est']+=est
json.dump(D,open('data21.json','w'),separators=(',',':'))
for o in est: print(f"{o['w']} {o['chip'][:30]:30} {o['dev'][:40]:40} {o['scene']:9} x={o['x']:<8} [{o['xlo']},{o['xhi']}] p={o['p']} e={o['e']} [{o['elo']},{o['ehi']}] q={o['q']}")
print(len(est),'rows; exceptions:',J['exceptions'] or 'none')
