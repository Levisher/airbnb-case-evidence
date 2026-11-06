"""Audit of the Google layer, one row per market. Reads price_map/raw/gmp, gmp_tests.json, gmp_tests2.json and the console record read on 6 Nov 2026. Makes no Google calls and holds market totals only, so no cell counts leave raw/gmp."""
import json,math,os,sys,numpy as np,pandas as pd
A=os.path.expanduser('~/Downloads/ABNB/'); sys.path.insert(0,A+'price_map/scripts')
import pm_gmp as g
from pm_loc import hav
W=g.W; D=A+'audit/'
T=json.load(open(D+'gmp_tests.json')); U=json.load(open(D+'gmp_tests2.json'))
c=pd.read_parquet(W+'cells.parquet'); c5=pd.read_parquet(W+'cells500.parquet'); B=pd.read_parquet(W+'beaches.parquet')
S=pd.read_csv(W+'sights.csv'); S=S[S.name!='AIRPORT']; d=pd.read_parquet(A+'price_map/out/homes_joined.parquet')
G=['restaurant','cafe_bar','grocery','sight','transit','hotel']
# Console, APIs and Metrics pages, 6 Nov 2026 11:32 UTC-5, identical on the 1-day and 30-day windows, whole project
CON=dict(console_aggregate_requests_all_markets=4844,console_aggregate_errors_all_markets=196,console_routes_requests_all_markets=4493,console_routes_errors_all_markets=98,billing_report_inr_1_to_6_nov=0.00,console_read='2026-11-06 11:32 UTC-5')
AGG_TIER=5000; RT_TIER=10000
def lost_run(x,m):
    """Elements the first 500 m run sent: its results were lost to a column-name bug, so the count is replayed from the same sights and beaches."""
    s=S[S.market==m].sort_values('reviews',ascending=False); b=B[B.market==m]; t=0
    for r in x.itertuples():
        dest=set()
        for k in (5,10,20):
            q=s.head(k); i=int(np.argmin(hav(r.lat,r.lon,q.lat.values,q.lon.values))); dest.add((q.lat.values[i],q.lon.values[i]))
        dd=hav(r.lat,r.lon,b.lat.values,b.lon.values); i=int(np.argmin(dd))
        if dd[i]<=2.5: dest.add((b.lat.values[i],b.lon.values[i]))
        t+=len(dest)
    return t
NAME={'lisbon':'Lisbon','maui':'Maui','san_diego':'San Diego','seattle':'Seattle'}
rows=[]
for m in ['lisbon','maui','san_diego','seattle']:
    fr=g.frame(m); fc,call=g.cells(fr); x=c[c.market==m]; y=c5[c5.market==m]; t=T[m]; u=U[m]; hj=d[d.market==m]; sp=u['splits']
    fail=(x[G]<0).sum().sum(); fcell=x[(x[G]<0).any(axis=1)]; fhomes=int(hj.cell.isin(fcell.cell).sum())
    e1=2*len(x); e2=lost_run(y,m); e3=int(y.nel.sum()); rf=int(y.w10.isna().sum()+((y.nel>1)&y.wb.isna()).sum()); rf1=int(x.drive_air_min.isna().sum()+x.walk_sight_min.isna().sum())
    pts=lambda a,b:round(100*(np.mean(sp[a])-np.mean(sp[b])),1); rng=lambda a,b:(round(100*min(np.subtract(sp[a],sp[b])),1),round(100*max(np.subtract(sp[a],sp[b])),1))
    gp=round(100*(t['r2_prop_google']-t['r2_prop']),1); gn=round(100*(t['r2_prop_neigh_google']-t['r2_prop_neigh']),1)
    r=dict(market=NAME[m],cells_1km_all=len(call),cells_1km_covered=len(x),min_homes_per_covered_cell=int(x.n.min()),homes_whole_frame=len(fr),homes_in_covered_cells=len(hj),homes_covered_pct=round(100*len(hj)/len(fr),1),
      aggregate_calls_logged=len(x)*len(G),aggregate_free_tier_monthly=AGG_TIER,aggregate_calls_pct_of_tier=round(100*len(x)*len(G)/AGG_TIER,1),
      routes_requests_logged=len(x)+math.ceil(len(x)/25)+2*len(y),routes_elements_1km_layer=e1,routes_elements_500m_lost_run=e2,routes_elements_500m_rerun=e3,routes_elements_total=e1+e2+e3,routes_free_tier_monthly=RT_TIER,routes_elements_pct_of_tier=round(100*(e1+e2+e3)/RT_TIER,1),**CON,
      aggregate_failed_after_retries=int(fail),aggregate_cells_with_a_failure=len(fcell),homes_in_failed_cells=fhomes,routes_elements_with_no_time=rf+rf1,
      no_google_hotel_700m_pct_of_homes=round(t['zero_cell_share'],1),no_hotel_700m_pct_if_failed_cell_has_none=round(t['zero_or_failed_share'],1),no_hotel_700m_pct_measured_from_home=round(t['home_none_700_covered'],1),no_hotel_500m_pct_measured_from_home=round(t['home_none_500_covered'],1),no_hotel_1000m_pct_measured_from_home=round(t['home_none_1000_covered'],1),no_hotel_700m_ceiling_pct_all_frame_homes=round(t['bound_all_uncovered_none'],1),no_osm_hotel_700m_pct=round(u['none_700_osm'],1),no_listing_file_hotel_room_700m_pct=round(u['none_700_hotelroom_listing'],1),
      homes_in_price_model=t['n'],r2_property_fields=round(t['r2_prop'],3),r2_property_plus_google=round(t['r2_prop_google'],3),r2_gain_pts_over_property=gp,r2_gain_pts_over_property_ci_low=round(100*t['gain_prop_lo'],1),r2_gain_pts_over_property_ci_high=round(100*t['gain_prop_hi'],1),
      r2_property_plus_neighbourhood=round(t['r2_prop_neigh'],3),r2_gain_pts_over_neighbourhood=gn,r2_gain_pts_over_neighbourhood_ci_low=round(100*t['gain_neigh_lo'],1),r2_gain_pts_over_neighbourhood_ci_high=round(100*t['gain_neigh_hi'],1),r2_listing_coordinates_1km_cell_ceiling=round(t['r2_prop_cell_ceiling'],3),
      heldout_r2_property=round(np.mean(sp['prop']),3),heldout_r2_neighbourhood=round(np.mean(sp['neigh']),3),heldout_r2_straight_line_distance=round(np.mean(sp['geom']),3),heldout_r2_google=round(np.mean(sp['google']),3),heldout_r2_google_counts_only=round(np.mean(sp['google_counts_only']),3),heldout_r2_neighbourhood_plus_google=round(np.mean(sp['neigh_google']),3),heldout_gain_pts_google_over_neighbourhood=pts('google','neigh'),heldout_gain_pts_added_to_neighbourhood=pts('neigh_google','neigh'),heldout_gain_pts_added_low=rng('neigh_google','neigh')[0],heldout_gain_pts_added_high=rng('neigh_google','neigh')[1])
    nm=NAME[m]; un=len(fr)-len(hj)
    fail_t={'lisbon':'Failures: no count failed in Lisbon, which says nothing about whether the counts are complete.','maui':'Failures: no count failed on Maui, which says nothing about whether the counts are complete.',
      'san_diego':f'Failures: {int(fail)} failed counts sit in {len(fcell)} cells holding {fhomes} homes, and none is a hotel count, so the hotel share is untouched while the amenity terms treat those cells as empty.',
      'seattle':f'Failures: {int(fail)} failed counts sit in {len(fcell)} cells holding {fhomes} homes. One is the hotel count of a 36-home cell, which the {r["no_google_hotel_700m_pct_of_homes"]}% treats as having a hotel, and the share moves to {r["no_hotel_700m_pct_if_failed_cell_has_none"]}% if that cell has none.'}[m]
    date_t={'maui':'Dating: Places shows operating places in November 2026, after the August 2023 Lahaina fire, so it cannot rebuild the Maui map of 2022 or any year before the fire.','lisbon':'Dating: Places shows operating places in November 2026, so it cannot say which Lisbon hotels, restaurants or sights existed in 2022, or which came before the homes around them.','san_diego':'Dating: Places shows operating places in November 2026, so it cannot say which San Diego hotels existed in 2022, or whether hotels closed or opened near these homes.','seattle':'Dating: Places shows operating places in November 2026, so it cannot say which Seattle hotels existed in 2022, or whether hotels closed or opened near these homes.'}[m]
    r2_t={'maui':f'R-squared: the {gp}-point gain falls to {gn} over the neighbourhood field, which has only {u["neigh_levels"]} labels on Maui, and rests on {len(x)} cells. Routed drive time carries it, and it shows association on asking prices. It cannot show that location causes price or how the premium moved since 2022.',
      }.get(m,f'R-squared: the {gp}-point gain falls to {gn} once the listing file\'s own neighbourhood field is in the model, and listing coordinates alone reach {r["r2_listing_coordinates_1km_cell_ceiling"]}. It shows association on asking prices. It cannot show that location causes price or how the premium moved since 2022.')
    r['failed_calls_handling']=f"Places Aggregate: each call retried up to 6 times, waiting 2 to 12 seconds, on 429, 500, 503 or a dropped connection. Calls still failing were stored as -1 and never re-pulled ({int(fail)} here). The price model reads -1 as zero, the 700 m share counts only exact zeros, and the few-hotel split reads -1 as a low count. Routes: {r['routes_elements_with_no_time']} elements returned no time and stay blank in the 500 m layer, which the price model does not use, and all 1 km times came back. The first 500 m run spent {e2} elements here and lost them to a column-name bug, so a smaller rerun replaced it."
    r['cannot_establish']=' '.join([date_t,
      f'Cells: covered cells hold 5 or more homes, so the {un} homes in thinner cells are unmeasured, and the homes file is a September 2026 snapshot.',
      'Calls: market figures are logged calls. The console splits neither retries nor errors by market, and it counts Routes requests while billing counts elements. The zero billing read came about 10.5 hours after the run, inside Google\'s stated reporting delay.',
      fail_t,
      f'Hotel share: the figure measures Google\'s hotel tag, which no one has audited by hand, from the centre of a 1 km cell. OpenStreetMap gives {r["no_osm_hotel_700m_pct"]}%, so the level depends on the source. It cannot show that homes and hotels serve different guests, or that a guest lacked a hotel option.',
      r2_t,
      f'Sample: the price model keeps {t["n"]} of {len(hj)} homes, those with a review score and a usable price, so it cannot speak for unreviewed homes.'])
    rows.append(r)
R=pd.DataFrame(rows); o=list(R.columns); o.remove('failed_calls_handling'); o.insert(o.index('routes_elements_with_no_time')+1,'failed_calls_handling'); R=R[o]; R.to_csv(D+'gmp_cells.csv',index=False); print(R.drop(columns=['cannot_establish']).T.to_string())
