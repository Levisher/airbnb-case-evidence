"""Audit of the 385 per rival per market design. One row per market and rival, from raw pulls, the rung-1 rows behind every overlap figure, Apify run logs and the Airbnb census. No new pulls.
Reported totals: Booking.com filter counts from run logs, Vrbo totalCount per box from run logs (stay 5 to 12 Dec 2026, 2 adults). Skew: 1 km cells ranked on census homes, against 2,000 random census draws of the same size."""
import csv,glob,json,math,os,re,sys,collections
import numpy as np,pandas as pd
from scipy.spatial import cKDTree
A=os.path.expanduser('~/Downloads/ABNB/'); P=A+'rival_overlap/'; D=A+'audit/'; sys.path.insert(0,P+'04_analysis/scripts')
import ro_common as r
MK=['san_diego','seattle','hawaii','lisbon']; TARGET=385; rng=np.random.default_rng(11)
BK_TOTAL={'san_diego':1479,'seattle':801,'lisbon':5381,'hawaii':8525}
TERM={'Baixa':'Baixa / Chiado','Chiado':'Baixa / Chiado','Belém':'Belém','Graça':'Gračac','Parque das Nações':'Parque das Nacoes','Kailua':'Kailua-Kona','Kona':'Kailua-Kona','Ko Olina':"Ko'Olina Resort"}
FOREIGN={'Belém':'Belém, Brazil','Gračac':'Gračac, Croatia'}
HT={'APA':'201','HOL':'220','Apartments':'201','Holiday homes':'220'}
L={x['run_id']:x for x in csv.DictReader(open(P+'00_admin/run_ledger.csv'))}
# log totals
bk={}; vb={}; unk=collections.Counter()
for k,x in L.items():
    f=D+f'apify_logs/{k}.log'
    if not os.path.exists(f): continue
    t=open(f,errors='ignore').read()
    if x['actor']=='booking-scraper':
        for T,fl,nm in re.findall(r'"resultsCount":(\d+),"filters":(\{.*?\}),"destination":\{"id":-?\d+,"name":"([^"]+)"',t):
            h=re.search(r'ht_id":(\d+)',fl)
            if h: bk.setdefault((nm.strip(),h.group(1)),int(T))
    elif int(x['rows'] or 0) in(104,390,494):
        for a,b,c,d,n in re.findall(r'page 0 bounds\(([-\d.]+),([-\d.]+)→([-\d.]+),([-\d.]+)\) → \d+ card\(s\) \(totalCount: (\d+)\)',t): vb[tuple(round(float(q),4) for q in (a,b,c,d))]=int(n)
def box(s):
    m=re.search(r'bbox:([-\d.]+),([-\d.]+),([-\d.]+),([-\d.]+)',str(s)); return tuple(round(float(q),4) for q in m.groups()) if m else None
def island(la,lo):
    return np.where(lo<-159,'Kauai',np.where(lo<-157.5,'Oahu',np.where(la<20.35,'Hawaii Island',np.where(lo<-156.75,'Molokai and Lanai','Maui'))))
def cells(lat,lon,la0):
    return (np.floor(lat/.009).astype(int)).astype(str)+'_'+(np.floor(lon/(.009/math.cos(math.radians(la0)))).astype(int)).astype(str)
def dissim(s,c): return .5*np.abs(s-c).sum()
man=json.load(open(P+'00_admin/sampling_manifest_FULL.json'))
rows=[]; extra={}
for m in MK:
    fr=r.frame(m).reset_index(drop=True); la0=fr.latitude.mean(); fr['cell']=cells(fr.latitude.values,fr.longitude.values,la0)
    n_c=fr.groupby('cell').size().sort_values(ascending=False); ncell=len(n_c); dec=pd.Series(np.minimum(10,np.arange(ncell)*10//ncell+1),index=n_c.index); top=set(dec[dec==1].index)
    fr['dec']=fr.cell.map(dec); cshare=fr.dec.value_counts(normalize=True).reindex(range(1,12),fill_value=0).values; top_c=cshare[0]*100
    fr['area']=fr.neighbourhood_cleansed.astype(str); fr['big']=island(fr.latitude.values,fr.longitude.values) if m=='hawaii' else (np.where(fr.neighbourhood_group_cleansed.eq('Lisboa'),'Lisboa','Outside Lisboa') if m=='lisbon' else 'all')
    tree=cKDTree(np.c_[fr.latitude.values,fr.longitude.values*math.cos(math.radians(la0))]); areas=fr.area.value_counts(normalize=True); cen_med=None
    c0=(fr.latitude.median(),fr.longitude.median()); hav=lambda a,b:6371*2*np.arcsin(np.sqrt(np.sin(np.radians(a-c0[0])/2)**2+np.cos(np.radians(a))*np.cos(np.radians(c0[0]))*np.sin(np.radians(b-c0[1])/2)**2))
    ckm=hav(fr.latitude.values,fr.longitude.values)
    g=pd.read_csv(P+f'02_interim/candidate_pairs/{m}_rung1.csv',dtype={'id':str}); g=g[~g.type.astype(str).str.contains('hotel|hostel|resort',case=False)]
    # raw rows with their source unit
    rawv=[]
    for f in sorted(glob.glob(P+f'01_raw/vrbo/{m}/VRBO_*_LISTINGS_*')):
        if 'FULL' in f or 'PILOT' in f:
            for i,x in enumerate(json.load(open(f))): rawv.append(dict(id=str(x.get('expediaPropertyId')),unit=box(x.get('rawInput')),lat=(x.get('coordinates') or {}).get('lat'),lng=(x.get('coordinates') or {}).get('lng')))
    rawv=pd.DataFrame(rawv); rawv['pos']=rawv.groupby('unit').cumcount()
    rawb=[]
    for f in sorted(glob.glob(P+f'01_raw/booking/{m}/BOOKING_*')):
        if 'FULL' in f or 'PILOT' in f:
            ty=re.search(r'_(APA|HOL)_',f)
            for x in json.load(open(f)):
                q=str(x.get('startUrlOrQuery')); rawb.append(dict(id=str(x.get('hotelId') or x.get('url')),term=q,ht=HT[ty.group(1)] if ty else None,order=x.get('order'),rating=x.get('rating'),reviews=x.get('reviews'),phase='PILOT' if 'PILOT' in f else 'FULL'))
    rawb=pd.DataFrame(rawb)
    for s,raw in [('vrbo',rawv),('booking',rawb)]:
        x=g[g.site==s].copy(); keyed=x[x.keyed]; n=len(x)
        la=x.lat.values.astype(float); lo=x.lng.values.astype(float); cc=cells(la,lo,la0); dd=pd.Series(cc).map(dec).fillna(11).astype(int).values
        sshare=np.bincount(dd,minlength=12)[1:12]/n; top_s=sshare[0]*100; off=sshare[10]*100; D_dec=dissim(sshare,cshare)*100
        # random-draw benchmark
        idx=rng.integers(0,len(fr),(2000,n)); dv=fr.dec.values; T=[];Dn=[]
        for q in idx:
            b=np.bincount(dv[q],minlength=12)[1:12]/n; T.append(b[0]*100); Dn.append(dissim(b,cshare)*100)
        lo_t,hi_t=np.percentile(T,[2.5,97.5]); d_hi=np.percentile(Dn,97.5)
        _,nn=tree.query(np.c_[la,lo*math.cos(math.radians(la0))]); ar=fr.area.values[nn]; bg=np.asarray(fr.big.values)[nn]
        if m=='hawaii': bg=island(la,lo)
        sa=pd.Series(ar).value_counts(normalize=True).reindex(areas.index,fill_value=0); D_area=dissim(sa.values,areas.values)*100
        Da=[]
        ai=pd.factorize(fr.area)[0]; order=pd.factorize(fr.area)[1]; cen=np.bincount(ai)/len(fr)
        for q in idx[:800]: Da.append(dissim(np.bincount(ai[q],minlength=len(cen))/n,cen)*100)
        da_hi=np.percentile(Da,97.5)
        # overlap by density band, then to census weights
        band=np.where(dd==1,'top',np.where(dd<=3,'mid','rest')); x['band']=band; x['big']=bg; x['dec']=dd
        cb={'top':cshare[0],'mid':cshare[1]+cshare[2],'rest':cshare[3:].sum()}
        k=x[x.keyed]; jb=k.groupby('band').hit.agg(['mean','size']); raw_rate=k.hit.mean()*100
        rw=sum(cb[b]*(jb['mean'].get(b,raw_rate/100)) for b in cb)*100
        jt=jb['mean'].get('top',np.nan)*100; jr=k[k.band!='top'].hit.mean()*100
        ab=fr.big.value_counts(normalize=True); ka=k.groupby('big').hit.agg(['mean','size']); present=[b for b in ab.index if b in ka.index and ka['size'][b]>=10]; miss_area=(1-sum(ab[b] for b in present))*100; rwa=sum(ab[b]*ka['mean'][b] for b in present)/sum(ab[b] for b in present)*100 if miss_area<=10 else None
        # overlap to the rival's own reported distribution
        if s=='vrbo':
            units=[box(b) for b in man['vrbo_boxes'][m]]; T_u={b:vb.get(b) for b in units}; known={b:t for b,t in T_u.items() if t}; fill=np.mean(list(known.values()))
            total=sum(known.values()); nu=len(T_u); nk=len(known); hitcap=int((raw[raw.unit.isin(units)].groupby('unit').size()>=13).sum())
            def where(a,c):
                for b in units:
                    if b[0]-.001<=a<=b[2]+.001 and b[1]-.001<=c<=b[3]+.001: return b
            x['unit']=[where(a,c) for a,c in zip(la,lo)]; cnt=x.groupby('unit').size(); x['w']=[(T_u.get(b) or fill)/cnt[b] if b in cnt.index else np.nan for b in x.unit]
            in_known=int(x.unit.isin(list(known)).sum())
            full=[b for b in units]; inbox=np.mean([ (b[0]-.002<=a<=b[2]+.002) and (b[1]-.002<=c<=b[3]+.002) for a,c,b in zip(raw.lat,raw.lng,raw.unit) if b and pd.notna(a)])*100
            design=f'{len(man["vrbo_boxes"][m])} boxes drawn from Airbnb density, 13 rows each'+(', plus 8 pilot boxes' if m=='san_diego' else ''); terms='boxes, no search terms'
            rp=raw.pos.values; pos=raw.drop_duplicates('id').set_index('id').pos; x['rank']=x.id.map(pos); hi_rank=x['rank']<6
            reached=in_known/total*100; rep=total; basis=f'sum of Vrbo totalCount over {nk} of {nu} boxes, homes open for a 5 to 12 Dec 2026 stay for 2 adults, so a count of available homes on the Airbnb-shaped boxes'
            term_reach=None
        else:
            rawb2=raw.copy(); rawb2['dest']=rawb2.term.map(lambda q:TERM.get(q,q)); rawb2['ht']=rawb2.ht.fillna('220')
            if m in('san_diego','seattle'):
                city='San Diego' if m=='san_diego' else 'Seattle'; rawb2['st']=rawb2.ht; Tm={h:bk[(city,h)] for h in('201','220')}
            else:
                rawb2['st']=rawb2.dest+'|'+rawb2.ht; Tm={}
                for q in rawb2.st.unique():
                    dn,h=q.split('|'); Tm[q]=bk.get((dn,h)) or bk.get(({'North Shore':'North Shore Oahu '}.get(dn,dn).strip(),h))
                Tm={q:t for q,t in Tm.items() if t and q.split('|')[0] not in FOREIGN}
            st=rawb2.drop_duplicates('id').set_index('id').st; x['unit']=x.id.map(st); cnt=x.groupby('unit').size()
            x['w']=[Tm.get(b,np.nan)/cnt[b] if b in cnt.index and b in Tm else np.nan for b in x.unit]
            total=BK_TOTAL[m]; rep=total; basis='Booking.com filter count, Apartments plus Holiday homes, may hold hotel-like units'; reached=n/total*100; term_reach=min(100.,sum(Tm.values())/total*100)
            planned=[q for q in man['queries'] if q[0]==m]; nu=len(planned); nk=len([q for q in planned if TERM.get(q[1],q[1]) not in FOREIGN]); hitcap=sum(1 for q in planned if len(raw[(raw.term==q[1])&(raw.ht==HT[q[2]])])>=q[4])
            ts=sorted({q[1] for q in planned}); bad=[f'{q} resolved to {FOREIGN[TERM.get(q,q)]}' for q in ts if TERM.get(q,q) in FOREIGN]; dup=[f'{q} resolved to {TERM[q]}' for q in ts if q in TERM and TERM[q] not in FOREIGN]
            design=f'{len(ts)} search terms by 2 property types, {nu} searches'+(', plus pilot district searches' if m=='san_diego' else ''); terms='; '.join(ts+bad+dup); inbox=None
            o=raw.drop_duplicates('id').set_index('id'); x['rank']=x.id.map(pd.to_numeric(o.order,errors='coerce')); hi_rank=x['rank']<=x.groupby('unit')['rank'].transform('median')
        kk=x[x.keyed&x.w.notna()]; rw_own=(kk.hit*kk.w).sum()/kk.w.sum()*100; own_rows=len(kk); kr=x[x.keyed&x['rank'].notna()]; hr=hi_rank.reindex(kr.index); early=kr[hr].hit.mean()*100; late=kr[~hr].hit.mean()*100
        allr=pd.read_csv(P+f'02_interim/candidate_pairs/{m}_rung1.csv',dtype={'id':str}); inb=int((allr.site==s).sum()); uq=raw.id.nunique(); outm=uq-inb; hot=inb-n
        e_n=int(hr.sum()); l_n=int((~hr).sum()); pz=(early-late)/100; pp=kr.hit.mean(); se=math.sqrt(pp*(1-pp)*(1/max(e_n,1)+1/max(l_n,1))); pval=math.erfc(abs(pz/se)/math.sqrt(2)) if se else 1
        row=dict(market=m,rival=s,design=design,search_terms=terms,units_planned=nu,units_with_reported_total=nk,units_hitting_row_cap=hitcap,rows_pulled_raw=len(raw),rows_unique=raw.id.nunique(),rows_outside_market=outm,rows_hotel_type_removed=hot,rows_behind_overlap=n,target_rows=TARGET,rows_pct_of_target=round(n/TARGET*100,1),keyed_rows=len(k),joined_rows=int(k.hit.sum()),joined_pct=round(raw_rate,1),
          reported_total=rep,reported_total_basis=basis,share_of_reported_total_pct=None if reached is None else round(reached,1),search_terms_reach_pct_of_total=None if term_reach is None else round(term_reach,1),
          census_homes=len(fr),census_cells_1km=ncell,census_share_densest_decile_pct=round(top_c,1),sample_share_densest_decile_pct=round(top_s,1),random_draw_low_pct=round(lo_t,1),random_draw_high_pct=round(hi_t,1),skew_gap_pts=round(top_s-top_c,1),sample_share_off_census_cells_pct=round(off,1),dissimilarity_density_deciles_pct=round(D_dec,1),dissimilarity_random_97_5_pct=round(d_hi,1),dissimilarity_neighbourhoods_pct=round(D_area,1),dissimilarity_neighbourhoods_random_97_5_pct=round(da_hi,1),median_km_from_centre_sample=round(float(np.median(hav(la,lo))),1),median_km_from_centre_census=round(float(np.median(ckm)),1),
          joined_pct_densest_decile=round(jt,1),joined_pct_other_cells=round(jr,1),joined_pct_reweighted_to_census_density=round(rw,1),joined_pct_reweighted_to_census_area=None if rwa is None else round(rwa,1),census_area_share_unsampled_pct=round(miss_area,1),joined_pct_reweighted_to_rival_totals=round(rw_own,1),keyed_rows_in_rival_reweight=own_rows,joined_pct_early_rank=round(early,1),joined_pct_late_rank=round(late,1),rank_gap_p_value=round(pval,3))
        if m=='lisbon':
            f2=fr[fr.big=='Lisboa']; n2=f2.groupby('cell').size().sort_values(ascending=False); d2=pd.Series(np.minimum(10,np.arange(len(n2))*10//len(n2)+1),index=n2.index); c2=f2.cell.map(d2).value_counts(normalize=True).reindex(range(1,12),fill_value=0).values
            sel=(bg=='Lisboa'); e2=pd.Series(cc[sel]).map(d2).fillna(11).astype(int).values; s2=np.bincount(e2,minlength=12)[1:12]/sel.sum()
            a2=f2.area.value_counts(normalize=True); s3=pd.Series(ar[sel]).value_counts(normalize=True).reindex(a2.index,fill_value=0)
            I=rng.integers(0,len(f2),(800,int(sel.sum()))); fa=pd.factorize(f2.area)[0]; cn=np.bincount(fa)/len(f2); B=[dissim(np.bincount(fa[q],minlength=len(cn))/sel.sum(),cn)*100 for q in I]
            extra[f'lisboa_only_{s}']=dict(rows=int(sel.sum()),census=len(f2),census_top=round(c2[0]*100,1),sample_top=round(s2[0]*100,1),d_neigh=round(dissim(s3.values,a2.values)*100,1),d_neigh_random=round(float(np.percentile(B,97.5)),1),cells_hit=int(pd.Series(cc[sel]).nunique()),census_cells=len(n2),top5=pd.Series(ar[sel]).value_counts(normalize=True).head(5).round(3).to_dict())
        if m=='seattle' and s=='booking':
            o=raw.drop_duplicates('id').set_index('id'); y=x.copy(); y['rt']=pd.to_numeric(y.id.map(o.rating),errors='coerce'); y['rv']=pd.to_numeric(y.id.map(o.reviews),errors='coerce').fillna(0); y['bay']=(y.rv*y.rt.fillna(0)+20*8.5)/(y.rv+20); y=y.sort_values('bay',ascending=False)
            rep_={}
            for N in (150,263,341):
                t_=y.head(N); kk_=t_[t_.keyed]; rep_[N]=dict(keyed=len(kk_),joined_pct=round(kk_.hit.mean()*100,1),key_share=round(len(kk_)/N*100,1))
            draws=[y.sample(263,random_state=i) for i in range(300)]; rr=[q[q.keyed].hit.mean()*100 for q in draws]; extra['seattle_replay']=dict(all=round(k.hit.mean()*100,1),top=rep_,random263=[round(float(v),1) for v in np.percentile(rr,[2.5,97.5])])
        rows.append(row); print(m,s,json.dumps({a:b for a,b in row.items() if a not in('design','search_terms','reported_total_basis')},default=str,ensure_ascii=False),flush=True)
        if s=='vrbo': print('   inbox',round(inbox,1),'cap',hitcap,flush=True)
        else: print('   terms',terms[:300],'Tm',str(Tm)[:400],flush=True)
        print('   big',k.groupby('big').hit.agg(['mean','size']).round(3).to_dict('index'),'census',ab.round(3).to_dict() if m in('hawaii','lisbon') else '',flush=True)
R=pd.DataFrame(rows)
w=R[['joined_pct','joined_pct_reweighted_to_census_density','joined_pct_reweighted_to_census_area','joined_pct_reweighted_to_rival_totals']]
R['joined_pct_low']=w.min(axis=1); R['joined_pct_high']=w.max(axis=1); R['joined_pct_spread_pts']=(R.joined_pct_high-R.joined_pct_low).round(1)
R['sampling_noise_pts']=(196*np.sqrt(R.joined_pct/100*(1-R.joined_pct/100)/R.keyed_rows)).round(1)
R['neighbourhood_excess_pts']=(R.dissimilarity_neighbourhoods_pct-R.dissimilarity_neighbourhoods_random_97_5_pct).round(1)
R['search_terms_reach_pct_of_total']=R.search_terms_reach_pct_of_total.fillna(100.0)
# rule: a rate goes directional when weights move it by more than its own sampling noise, or the searches could reach under half of the rival's total
dirn=(R.joined_pct_spread_pts>R.sampling_noise_pts)|(R.search_terms_reach_pct_of_total<50)
FL=R.market.isin(['hawaii','lisbon'])
R['overlap_status']=np.where(dirn,'directional',np.where(FL,'holds as a sample floor','holds as a sample rate'))
WHY={('san_diego','vrbo'):'Weights move the rate 0.9 points. 345 rows missed the 385 target, and the boxes follow Airbnb density by design, so the census match is built in.',
('san_diego','booking'):'Weights move the rate 0.1 points, but one city search sorted by review score reached 23.1% of the total, so the rate describes well-reviewed homes first.',
('seattle','vrbo'):'Weights move the rate 1.1 points on the widest Vrbo reach of the four markets, 35.8% of homes open that week.',
('seattle','booking'):'Near-census at 96.5% of the reported total, so the gap against Airbnb shows Booking.com\'s real footprint and sets the benchmark for the other markets.',
('hawaii','vrbo'):'Weights move the rate 1.3 points, and rates run from 32.0% on Hawaii Island to 75.8% on Kauai. The logs give no Vrbo total for 19 of 38 boxes.',
('hawaii','booking'):'Weights move the rate 6.4 points against 5.1 of noise, with 14 rows a search and Kailua resolving to Kailua-Kona, so the windward Oahu search never ran. 69.4% is not a floor, since census density weights give 67.7%.',
('lisbon','vrbo'):'Weights move the rate 1.7 points. Rows early in each box join at 66.2% against 81.9% later (p 0.001, dataset order only), so the cap may understate and the floor wording stays safe.',
('lisbon','booking'):'Least representative cell. 263 rows missed the target, 70 rows came from Belem in Brazil and Gracac in Croatia, searches reach 38.3% of the total, and 2 keyed rows sit outside Lisboa against 31.5% of the census. The rate describes central Lisbon only.'}
R['audit_reason']=[WHY[(a,b)] for a,b in zip(R.market,R.rival)]
R.to_csv(D+'sampling_audit.csv',index=False); json.dump(extra,open(D+'sampling_tests.json','w'),indent=1,ensure_ascii=False); print(R[['market','rival','joined_pct','joined_pct_low','joined_pct_high','joined_pct_spread_pts','sampling_noise_pts','neighbourhood_excess_pts','overlap_status']].to_string())
