"""Apify helpers for the dated price map pulls. Every run is logged to raw/run_ledger.csv with its cost."""
import json,os,ssl,subprocess,time,urllib.request,certifi,csv
ctx=ssl.create_default_context(cafile=certifi.where())
P=os.path.expanduser('~/Downloads/ABNB/price_map/')
def tok(): return subprocess.check_output([os.path.expanduser('~/.local/bin/apify-key')]).decode().strip()
def api(path,data=None):
    q=urllib.request.Request('https://api.apify.com/v2/'+path,headers={'Authorization':'Bearer '+tok(),'Content-Type':'application/json'},data=json.dumps(data).encode() if data is not None else None)
    return json.load(urllib.request.urlopen(q,context=ctx,timeout=60))
def run(act,inp,cap,name,timeout=600):
    r=api(f"acts/{act.replace('/','~')}/runs?maxTotalChargeUsd={cap}",inp)['data']; i=r['id']; t0=time.time()
    while time.time()-t0<timeout:
        s=api('actor-runs/'+i)['data']
        if s['status'] not in('READY','RUNNING'): break
        time.sleep(5)
    if s['status'] in('READY','RUNNING'): api(f'actor-runs/{i}/abort',{}); s=api('actor-runs/'+i)['data']
    rows=[];off=0
    while True:
        b=api(f"datasets/{s['defaultDatasetId']}/items?format=json&clean=false&offset={off}&limit=500") if False else None
        q=urllib.request.Request(f"https://api.apify.com/v2/datasets/{s['defaultDatasetId']}/items?format=json&clean=false&offset={off}&limit=500",headers={'Authorization':'Bearer '+tok()})
        b=json.load(urllib.request.urlopen(q,context=ctx,timeout=120))
        rows+=b; off+=len(b)
        if len(b)<500: break
    json.dump(rows,open(P+f'raw/{name}.json','w'))
    with open(P+'raw/run_ledger.csv','a',newline='') as f: csv.writer(f).writerow([i,act,name,s.get('finishedAt'),s['status'],len(rows),s.get('usageTotalUsd'),json.dumps(inp)[:300]])
    return s['status'],rows,s.get('usageTotalUsd')
