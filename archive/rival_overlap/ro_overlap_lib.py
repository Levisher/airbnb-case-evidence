import glob,re
import pandas as pd,ro_common as r
RAD={'vrbo':520,'booking':200}
def toks(m,s):
    if m=='lisbon': return set(re.findall(r'(\d{3,7})\s*/\s*AL',str(s),re.I))
    o=set()
    for t in re.findall(r'[A-Za-z0-9][A-Za-z0-9\-/\.]{3,}',str(s)):
        u=re.sub(r'[^A-Z0-9]','',t.upper())
        if len(u)>=5 and re.search(r'\d',u): o.add(u)
    return o
def air(m):
    a=pd.read_csv(r.P+'01_raw/quarantine_20261105/airbnb/lisbon.csv.gz',low_memory=False) if m=='lisbon' else pd.read_parquet(sorted(glob.glob(r.G+r.M[m][0]+'_*.parquet'))[-1])
    for k in ['latitude','longitude','bedrooms','minimum_nights','calculated_host_listings_count']: a[k]=pd.to_numeric(a[k],errors='coerce')
    a['k']=[toks(m,l) if pd.notna(l) else set() for l in a.license]
    a['elig']=(a.minimum_nights<30)&a.room_type.eq('Entire home/apt')
    return a
