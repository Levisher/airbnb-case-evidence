"""Size the partial rival pulls' effect on 'absent from Booking and Vrbo', Seattle and San Diego. Vrbo-only homes are scaled up by the pull's share of Vrbo's reported total, assuming unseen rows match Airbnb homes at the sample rate and repeat none already found."""
import json,os,sys,numpy as np,pandas as pd
A=os.path.expanduser('~/Downloads/ABNB/'); sys.path.insert(0,A+'rival_overlap/04_analysis/scripts')
R=pd.read_csv(A+'audit/sampling_audit.csv').set_index(['market','rival']); H=pd.read_parquet(A+'price_map/out/excl_homes.parquet'); out={}
for m in ['seattle','san_diego']:
    e=H[H.mkt==m]; N=len(e); fv=R.loc[(m,'vrbo'),'share_of_reported_total_pct']/100; vo=e[(e.vr==1)&(e.bk==0)]; bk=int(e.bk.sum()); nt=e.n.sum()
    out[m]=dict(homes=N,on_booking=bk,vrbo_only=len(vo),absent_pct=round(100*(1-e.sh.mean()),1),vrbo_share_pct=round(fv*100,1),absent_pct_vrbo_scaled=round(100*(N-bk-len(vo)/fv)/N,1),absent_nights_pct=round(100*e[e.sh==0].n.sum()/nt,1),absent_nights_pct_vrbo_scaled=round(100*(1-e[e.bk==1].n.sum()/nt-vo.n.sum()/fv/nt),1))
    print(m,out[m])
json.dump(out,open(A+'audit/sampling_excl.json','w'),indent=1)
