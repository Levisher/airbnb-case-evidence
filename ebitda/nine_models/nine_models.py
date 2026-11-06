"""The nine case companies on one frame. Compustat levels stay out, so this folder holds ratios only and every count is rebuilt from them."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
f = pd.read_csv(H / 'nine_frame_ratios.csv'); c = f[f.case_company == True]; R['frame_rows'] = len(f); R['frame_tickers'] = f.tic.nunique(); R['case_companies'] = c.tic.nunique(); R['case_company_margin_swings'] = c.swing_gt_5pts.sum()
v = c.drop_duplicates('tic').volume_tie_class.value_counts(); R['volume_ties_transacted'] = v.get('transacted value', 0); R['volume_ties_definitional'] = v.get('definitional', 0)
n = pd.read_csv(H / 'nine_growth.csv').set_index('t'); R['gross_after_marketing_airbnb'] = n.gross_after_mkt['ABNB']; R['gross_after_marketing_next'] = n.gross_after_mkt.drop('ABNB').max(); R['gross_after_marketing_rank'] = n.gross_after_mkt.rank(ascending=False)['ABNB']
save(__file__, R)
fig = plt.figure(figsize=(9, 4.2)); titled(fig, 'Airbnb keeps 61.8% of revenue after cost of revenue and marketing, the most of the models tested', 'Share of revenue after cost of revenue and marketing, FY2025. PayPal reports no cost line to compare')
ax = fig.add_axes([0.1, 0.13, 0.87, 0.68]); t = n.gross_after_mkt.dropna().sort_values(); t = t[t.index.isin(['ABNB', 'EBAY', 'ETSY', 'W', 'SNAP', 'PINS', 'ROKU', 'CART'])]; names = dict(ABNB='Airbnb', EBAY='eBay', ETSY='Etsy', W='Wayfair', SNAP='Snap', PINS='Pinterest', ROKU='Roku', CART='Instacart'); ax.barh([names[i] for i in t.index], t.values, color=[NAVY if i == 'ABNB' else BLUE for i in t.index], height=.62)
for i, x in enumerate(t.values): ax.text(x + .6, i, f'{x:.1f}%', va='center', fontsize=9)
ax.set_xlim(0, 75); ax.set_xlabel('Share of revenue, %')
finish(fig, __file__, 'nine_models.png')
