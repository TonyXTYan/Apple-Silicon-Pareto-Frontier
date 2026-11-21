"""Rebuild data and the page. Run from this folder: python3 build.py"""
import subprocess, sys, json, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
steps=['gen_data.py','model.py','llm.py','blender.py','i9.py','llm2.py','llm3.py','games.py','numerics.py','x86.py','llm4.py','cpubench.py','m4max14.py']   # data.json -> data2 ... -> data13.json
for s in steps:
    print('==',s,flush=True); subprocess.run([sys.executable,s],check=True,stdout=subprocess.DEVNULL)
t=open('template.html').read(); d=open('data13.json').read()
assert '/*DATA*/' in t
open('index.html','w').write(t.replace('/*DATA*/',d)); print('wrote index.html',len(t)+len(d),'bytes')
