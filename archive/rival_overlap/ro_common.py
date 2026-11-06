"""Shared helpers for the rival overlap pulls: market frames, density boxes, ledger, Apify launch and save."""
import csv,glob,json,math,os,re,time,urllib.request
import lr_common as c
P=os.path.expanduser('~/Downloads/ABNB/rival_overlap/')
G=os.path.expanduser('~/Downloads/ABNB/inventory/raw_regions/')
M={'san_diego':('united-state__san-diego','San Diego'),'seattle':('united-state__seattle','Seattle'),'hawaii':('united-state__hawaii','Hawaii'),'lisbon':(None,'Lisbon')}
def frame(m):
    import pandas as pd
    if m=='lisbon':
        d=pd.read_csv(P+'01_raw/quarantine_20261105/airbnb/lisbon.csv.gz',low_memory=False)
    else:
        d=pd.read_parquet(sorted(glob.glob(G+M[m][0]+'_*.parquet'))[-1])
    for k in ['latitude','longitude','minimum_nights','bedrooms','accommodates']:
        d[k]=pd.to_numeric(d[k],errors='coerce')
    return d[(d.minimum_nights<30)&d.room_type.eq('Entire home/apt')&d.latitude.notna()].copy()
def boxes(d,n):
    """Split the Airbnb frame by median until n boxes, so each box holds a similar number of eligible homes."""
    parts=[d]
    while len(parts)<n:
        parts.sort(key=len,reverse=True); p=parts.pop(0)
        la=p.latitude.max()-p.latitude.min(); lo=(p.longitude.max()-p.longitude.min())*math.cos(math.radians(p.latitude.mean()))
        k='latitude' if la>=lo else 'longitude'; v=p[k].median()
        parts+= [p[p[k]<=v],p[p[k]>v]]
    return [f"bbox:{p.latitude.min()-.0005:.4f},{p.longitude.min()-.0005:.4f},{p.latitude.max()+.0005:.4f},{p.longitude.max()+.0005:.4f}" for p in parts]
def launch(act,cap,inp):
    r=c.api(f'acts/{act}/runs?maxTotalChargeUsd={cap}',data=inp); d=r.get('data') or {}
    return d.get('id'),d.get('defaultDatasetId'),r.get('body','')[:200]
def wait_save(jobs,timeout=5400):
    """jobs: dicts with run, dataset, path. Saves each dataset once its run ends. Returns jobs with status, rows, usd."""
    t0=time.time(); left=list(jobs)
    while left and time.time()-t0<timeout:
        for j in list(left):
            d=c.api('actor-runs/'+j['run']).get('data') or {}
            if d.get('status') in('SUCCEEDED','FAILED','ABORTED','TIMED-OUT'):
                items=[];off=0
                while True:
                    q=urllib.request.Request(f"https://api.apify.com/v2/datasets/{j['dataset']}/items?format=json&clean=false&offset={off}&limit=500",headers={'Authorization':'Bearer '+c.token()})
                    b=json.loads(urllib.request.urlopen(q,timeout=180).read())
                    if not b: break
                    items+=b; off+=len(b)
                os.makedirs(os.path.dirname(j['path']),exist_ok=True); json.dump(items,open(j['path'],'w'))
                j.update(status=d['status'],rows=len(items),usd=round(d.get('usageTotalUsd') or 0,4),started_utc=d.get('startedAt'))
                ledger(j); left.remove(j); print(time.strftime('%T'),os.path.basename(j['path']),j['status'],j['rows'],j['usd'],flush=True)
        time.sleep(15)
    return jobs
def ledger(j):
    p=P+'00_admin/run_ledger.csv'
    with open(p,'a',newline='') as f:
        csv.writer(f).writerow([j['run'],j['actor'],j.get('started_utc'),j.get('status'),j.get('rows'),j.get('usd'),j.get('cap'),j.get('phase')])
