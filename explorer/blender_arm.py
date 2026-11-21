"""-> data19.json  Blender (Cycles) rows for the Arm comparison chips, from blender_arm_rows.json (id = position in that list).
Qualcomm: per-scene rows (monster, junkshop, classroom) for the Snapdragon X Elite X1E-84-100, from the one Blender 4.5.0
Open Data run of that chip (Windows on Arm). They reuse the power, power range and speed spread of its three-scene point
(nv2.py: 0.9 to 1.1 times the Galaxy Book4 Edge 16's Cinebench all-core wall power, est+pe, graded 'B'), as the Apple
scene rows reuse theirs. Ampere: nothing defensible (no Linux-aarch64 Open Data launcher; see `skipped` in the rows file).
Adreno: Cycles has no backend for it, so there are no GPU rows."""
import json, math
D=json.load(open('data18.json')); J=json.load(open('blender_arm_rows.json')); X={r['id']:r for r in J['rows']}
url2key={v['url']:k for k,v in D['sources'].items()}
SCENES=('monster','junkshop','classroom')
est=[]
for chip in sorted({r['chip'] for r in X.values()}):
    rs=[r for r in X.values() if r['chip']==chip]; v=rs[0]['vendor']; c=v+' '+chip
    t=next(r for r in D['est'] if r['w']=='bl-cpu' and r['chip']==c and not r.get('scene'))   # the three-scene point
    assert abs(sum(r['x_spm'] for r in rs)/60-t['x'])<0.002, 'scenes must sum to the three-scene score of the same run'
    assert [r['scene'] for r in rs]==list(SCENES)
    sx=math.log(t['xhi']/t['xlo'])/2; sP=math.log(t['phi']/t['plo'])/2; s=math.sqrt(sx*sx+sP*sP)
    for r in rs:
        u=r['url']; assert u in url2key; x=r['x_spm']/60; e=x/t['p']; n=r['n']
        note=(f"Render speed measured (Blender Open Data, the {r['scene']} scene of the one Blender {r['blender']} run of the {chip.split(' ')[-1]}: {r['samples']} samples in {r['time_for_samples_s']:.1f} s, {r['system']}); "
              f"wall power as for its three-scene point: 0.9 to 1.1 times the Cinebench all-core wall power of the Galaxy Book4 Edge 16 ({t['p']:g} W), the same rule as for the Apple chips. "
              "Each scene is assumed to draw the same power as the three-scene run. "
              f"Weaker: one run. The same chip's one Blender 4.4.0 run gave {r['earlier_run_4_4_0_spm']:.1f} samples per minute in this scene (not used). "
              'The median mixes chassis and power limits, so it need not match the machine whose power is borrowed.')
        o={k:t[k] for k in ('w','chip','dev','tier','form','resc','sl','sd','ck','gen','p','plo','phi','est','pe','seen')}
        o.update(x=round(x,3),xlo=round(x*math.exp(-sx),3),xhi=round(x*math.exp(sx),3),e=round(e,4),elo=round(e*math.exp(-s),4),ehi=round(e*math.exp(s),4),
                 src=url2key[u],q='B',bench=f"Blender {r['blender']} CPU, {r['scene']} scene, Open Data, {n} run, {r['x_spm']:.1f} samples/min (device \"{r['device']}\")",
                 note=note,scene=r['scene'])
        est.append(o)
D['est']+=est
json.dump(D,open('data19.json','w'),separators=(',',':'))
for o in est: print(f"{o['w']} {o['chip']} {o['scene']:9} x={o['x']} [{o['xlo']},{o['xhi']}] p={o['p']} [{o['plo']},{o['phi']}] e={o['e']} [{o['elo']},{o['ehi']}] q={o['q']}")
print('skipped:',', '.join(J['skipped']))
