"""Regression helpers shared by the two gmp test scripts."""
import numpy as np,pandas as pd
Ls=['l_restaurant','l_cafe_bar','l_grocery','l_sight','l_transit','l_hotel','l_walk','l_air']
def prop(v):
    return np.column_stack([v.bedrooms,v.accommodates,v.review_scores_rating,np.log1p(v.number_of_reviews),np.log1p(v.calculated_host_listings_count)])
def dummies(s):
    return pd.get_dummies(s.astype(str),drop_first=True).values.astype(float)
def ols(Xa,y,Xb=None):
    Xa=np.column_stack([np.ones(len(Xa)),Xa]); b=np.linalg.lstsq(Xa,y,rcond=None)[0]
    if Xb is None: return Xa@b
    return np.column_stack([np.ones(len(Xb)),Xb])@b
def r2(y,f): return 1-((y-f)**2).sum()/((y-y.mean())**2).sum()
