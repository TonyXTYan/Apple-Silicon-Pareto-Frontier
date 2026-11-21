"""-> data13.json  Estimated MacBook Pro 14 with M4 Max. No review metered this machine at the wall (research notes: no
Notebookcheck, ComputerBase, Max Tech, Ars, Macworld or LaptopMedia measurement), so its rows borrow the speed of the
MacBook Pro 16 with M4 Max measured on this page (Cinebench 2024 all-core and single-thread, Cyberpunk 2077, Baldur's
Gate 3, AC Shadows) and estimate the wall power: the 16-inch's wall power capped at the 14-inch's 96 W adapter envelope
(97 W, as Notebookcheck saw 98.1 W peak from an M4 Pro MacBook Pro 14 on the same adapter and about 97 W input on the
M5 Max MacBook Pro 14), with a range from 0.85 times that value up to the 16-inch's reading. No source quantifies how
much slower the 14-inch runs at that cap, so the speeds are kept and each note says the true speed is likely a bit lower."""
import json, math
D=json.load(open('data12.json'))
CAP=97.0      # W at the wall: the 96 W adapter envelope (98.1 W peak seen on the M4 Pro 14, ~97 W input limit on the M5 Max 14)
LO=0.85       # lower end of the power range, as a fraction of the central value
DEV16,DEV14='MacBook Pro 16','MacBook Pro 14'
src16=[r for r in D['rows']+D['est'] if r['chip']=='M4 Max' and r['dev']==DEV16 and not r.get('bm') and r['w'] in ('cpu-all','cpu-one','gpu')]
NBC14='https://www.notebookcheck.net/Apple-MacBook-Pro-14-2024-review-The-M4-Pro-and-matte-display-are-massive-upgrades.914597.0.html'
D['sources']['nbc_m4pro14']=dict(name='Notebookcheck, MacBook Pro 14 (2024) M4 Pro review',url=NBC14)
COMMON=(' No wall measurement exists for the 14-inch MacBook Pro with M4 Max: speed and power here are estimates, not readings of this machine.'
        ' Speed is borrowed from the 16-inch (16-core CPU, 40-core GPU, the same configuration the 14-inch offers at the top); the 14-inch has a smaller cooler and a 96 W adapter, '
        'so its sustained multi-core and GPU speed is likely a bit lower, but no source found measures by how much, so the speed is not scaled.'
        ' Apple\'s own figures for this machine are the ENERGY STAR record (A3185), shown with the point.')
rows=[]
for b in src16:
    w=b['w']; x=b['x']; p16=b['p']; ph16=b['phi'] if b.get('phi') else p16
    capped=p16>CAP; P=min(p16,CAP); plo=round(LO*P,1); phi=round(max(ph16,p16),1)
    sx=math.log(b['xhi']/b['xlo'])/2 if b.get('xlo') and b.get('xhi') and b['xhi']>b['xlo'] else 0.0
    e=x/P; elo=x/phi*math.exp(-sx); ehi=x/plo*math.exp(sx)
    what={'cpu-all':'Cinebench 2024 all-core','cpu-one':'Cinebench 2024 single-thread','gpu':(b.get('game') or 'Cyberpunk 2077')}[w]
    borrowed=('its Cyberpunk 2077 reading, which this page also uses for '+b['game'] if w=='gpu' and b.get('game')!='Cyberpunk 2077' else 'the '+what+' run')
    if w=='cpu-one':
        pw=(f"Power estimated: the 16-inch's single-thread wall power ({p16:g} W, {b['plo']:g} to {ph16:g} W) is far below the 14-inch's 96 W adapter, so it is kept, "
            f"with the range taken down to 0.85 times ({plo:g} W) for the 14-inch's smaller display and fans.")
    elif capped:
        pw=(f"Power estimated: the 16-inch drew {p16:g} W at the wall in {borrowed}"
            +(" (Notebookcheck's M5 GPU analysis; its original M4 Max review gave 107.2 W with an external monitor)" if w=='gpu' else '')
            +f", more than the 14-inch's 96 W adapter delivers, so the central value is capped at {CAP:g} W (Notebookcheck saw an M4 Pro MacBook Pro 14 peak at 98.1 W on the same adapter, "
            f"and Apple limits the M5 Max MacBook Pro 14 to about 97 W input). The range runs from {plo:g} W (0.85 times) up to the 16-inch's {phi:g} W, because the battery can cover a demand above the adapter, "
            "which this efficiency would then overstate.")
    else:
        pw=(f"Power estimated: the 16-inch drew {p16:g} W at the wall in {borrowed} ({b['plo']:g} to {ph16:g} W), within the 14-inch's 96 W adapter, so it is kept as the central value; "
            f"the range runs from {plo:g} W (0.85 times, for a 14-inch that throttles to a lower sustained power) up to the 16-inch's {phi:g} W peak, which is above what the adapter delivers.")
    note=f"Speed borrowed from the 16-inch: {what} as measured by Notebookcheck on the MacBook Pro 16 with M4 Max ({x:g} {'fps' if w=='gpu' else 'points'}). "+pw+COMMON
    r=dict(w=w,chip='M4 Max',ck='M4 Max',gen=4,dev=DEV14,tier='Max',form='laptop',x=x,e=round(e,4),elo=round(elo,4),ehi=round(ehi,4),
           p=P,plo=plo,phi=phi,q='B',est=1,pe=1,seen=True,brw=DEV16,src=b['src'],psrc='nbc_m4pro14',resc=False,bench=b['bench']+' (speed of the MacBook Pro 16)',note=note)
    if b.get('xlo'): r.update(xlo=b['xlo'],xhi=b['xhi'])
    if w=='gpu': r['game']=b['game']
    rows.append(r)
assert len(rows)==5, len(rows)
D['est']+=rows
json.dump(D,open('data13.json','w'),separators=(',',':'))
for r in rows: print(f"{r['w']:7} {r.get('game',''):25} x={r['x']:7} P={r['p']:5} [{r['plo']},{r['phi']}] e={r['e']} [{r['elo']},{r['ehi']}]")
