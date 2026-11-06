"""Airbnb, Vacasa and Sonder on $100 of guest bookings, FY2024, read straight from the 10-K text.

Every amount is parsed from the filing by its line label, then footed to the filing's own total costs
and operating result. Nothing comes from the earlier table. Sonder reports no bookings, so it appears on
revenue and on an estimated bookings base, which adds back the taxes it excludes from revenue.
Writes per100_peers.csv (the lines) and per100_gap_split.csv (the gap split and Sonder's trend).
"""
import csv, os, re
R = os.path.expanduser('~/Downloads/ABNB/operating_leverage/raw/')
OUT = os.path.expanduser('~/Downloads/ABNB/reverse_eng/')
F = {'Airbnb': ('ABNB/2025-02-13_10-K.txt', '10-K FY2024, filed 13 Feb 2025', '0001559720-25-000010'),
     'Vacasa': ('VCSA/2025-03-13_10-K.txt', '10-K FY2024, filed 13 Mar 2025', '0001874944-25-000003'),
     'Sonder': ('SOND/2025-07-24_10-K.txt', '10-K FY2024, filed 24 Jul 2025', '0001819395-25-000088')}
TAX = (0.14, 0.10, 0.20)   # proxy lodging-tax rates for the Sonder bookings base, not disclosed by Sonder


def flat(f):
    t = open(R + f, errors='ignore').read().replace('\xa0', ' ').replace('​', '')
    return re.sub(r'\s+', ' ', t)


def num(s):
    s = s.replace(',', '').replace('$', '').replace('(', '').replace(')', '').strip()
    return 0.0 if s in ('—', '-') else float(s)


def after(t, anchor, label, col, n=8, last=True):
    """nth numeric column following a label, searched after the last hit of a statement anchor"""
    i = [m.start() for m in re.finditer(anchor, t)][-1 if last else 0]
    j = t.index(label, i) + len(label)
    v = re.findall(r'\(? ?[\d,]*\d(?:\.\d+)? ?\)?|—', t[j:j + 120])
    return num(v[col])


txt = {k: flat(v[0]) for k, v in F.items()}
a, v, s = txt['Airbnb'], txt['Vacasa'], txt['Sonder']
AS, VS, SS = 'Consolidated Statements of Operations \\(in millions', 'Consolidated Statements of Operations \\(in thousands', 'CONSOLIDATED STATEMENTS OF OPERATIONS AND COMPREHENSIVE LOSS Years ended'
A = {k: after(a, AS, l, 2) for k, l in dict(rev='Revenue', cogs='Cost of revenue', ops='Operations and support', pd='Product development', sm='Sales and marketing', ga='General and administrative', tot='Total costs and expenses', oi='Income from operations').items()}
K = 1000.0
Vv = {k: after(v, VS, l, 0) / K for k, l in dict(rev='Revenue', cogs='Cost of revenue, exclusive of depreciation and amortization shown separately below', ops='Operations and support', tech='Technology and development', sm='Sales and marketing', ga='General and administrative', dep='Depreciation', am='Amortization of intangible assets', imp='Impairment of long-lived assets', tot='Total operating costs and expenses', oi='Loss from operations').items()}
S = {k: after(s, SS, l, 0) / K for k, l in dict(rev='Revenue', cogs='Cost of revenue (excluding depreciation and amortization)', ops='Operations and support', ga='General and administrative', rd='Research and development', sm='Sales and marketing', imp='Impairment losses', integ='Integration costs', restr='Restructuring and other charges', tot='Total costs and operating expenses', oi='Loss from operations').items()}
assert abs(A['cogs'] + A['ops'] + A['pd'] + A['sm'] + A['ga'] - A['tot']) < .5 and abs(A['rev'] - A['tot'] - A['oi']) < .5
assert abs(sum(Vv[k] for k in ('cogs', 'ops', 'tech', 'sm', 'ga', 'dep', 'am', 'imp')) - Vv['tot']) < .01 and abs(Vv['rev'] - Vv['tot'] + Vv['oi']) < .01
assert abs(sum(S[k] for k in ('cogs', 'ops', 'ga', 'rd', 'sm', 'imp', 'integ', 'restr')) - S['tot']) < .01 and abs(S['rev'] - S['tot'] + S['oi']) < .01
Vv['oi'], S['oi'] = -Vv['oi'], -S['oi']   # both filings print the loss line as a positive amount
g = lambda t, p, grp=1: num(re.search(p, t).group(grp))
A['gbv'] = g(a, r'Gross Booking Value \$? ?[\d,]+ \$? ?([\d,]+)')
A['sbc'] = g(a, r'Stock-based compensation expense \$? ?[\d,]+ 100 % \$? ?([\d,]+) 100')
Vv['gbv'] = g(v, r'GBV \$ ([\d,]+) \$') / K
Vv['sbc'] = g(v, r'Equity-based compensation ([\d,]+) [\d,]+ [\d,]+ Business combination') / K
Vv['other'] = g(v, r'Other services ([\d,]+) [\d,]+ [\d,]+ Total') / K
Vv['restr'] = g(v, r'Restructuring \(2\) ([\d,]+) ') / K
S['sbc'] = g(s, r'Stock-based compensation ([\d,]+) [\d,]+ Lease adjustment') / K
S['nrp'] = g(s, r'Non-recurring professional fees ([\d,]+) ') / K
S['da'] = g(s, r'Depreciation and amortization expense ([\d,]+) ') / K
S['lease'] = g(s, r'Operating lease cost \$ ([\d,]+) \$') / K
S['ebitda'] = -g(s, r'Adjusted EBITDA \$ \(([\d,]+)\) \$') / K
S['vat'] = g(s, r'a \$([\d.]+) million increase in taxes primarily related to value added taxes')
S['bad'] = g(s, r'a \$([\d.]+) million increase in bad debt expense')
FS = 'Consolidated Statements of Operations'
rows = []


def add(co, basis, item, amt, den, line, where, note=''):
    f = F[co]
    rows.append(dict(company=co, basis=basis, line_item=item, usd_m=round(amt, 3), denominator_usd_m=round(den, 3), per_100=round(amt / den * 100, 2),
                     filing_line=line, filing=f[1], location=where, accession=f[2], note=note))


def block(co, basis, den, L):
    rev, direct, ops, sm, ovh, spec, oi = (L[k] for k in ('rev', 'direct', 'ops', 'sm', 'ovh', 'spec', 'oi'))
    n = L['notes']; w = L['where']
    add(co, basis, 'revenue_kept', rev[0], den, rev[1], w, n.get('rev', ''))
    add(co, basis, 'direct_costs', direct[0], den, direct[1], w, n.get('direct', ''))
    add(co, basis, 'support_and_operations', ops[0], den, ops[1], w, n.get('ops', ''))
    add(co, basis, 'left_after_direct_and_support', rev[0] - direct[0] - ops[0], den, 'calculated: revenue less the two lines above', 'calculated')
    add(co, basis, 'sales_and_marketing', sm[0], den, sm[1], w, n.get('sm', ''))
    add(co, basis, 'left_after_sales_and_marketing', rev[0] - direct[0] - ops[0] - sm[0], den, 'calculated', 'calculated')
    add(co, basis, 'overhead_and_stock_pay', ovh[0], den, ovh[1], w, n.get('ovh', ''))
    add(co, basis, 'operating_income_before_special_lines', rev[0] - direct[0] - ops[0] - sm[0] - ovh[0], den, 'calculated', 'calculated')
    add(co, basis, 'special_lines', spec[0], den, spec[1], w, n.get('spec', ''))
    add(co, basis, 'operating_income_gaap', oi[0], den, oi[1], w, 'Foots to the filing total')
    for it, amt, ln, wh, nt in L['memo']:
        add(co, basis, it, amt, den, ln, wh, nt)


LA = dict(rev=(A['rev'], 'Revenue'), direct=(A['cogs'], 'Cost of revenue'), ops=(A['ops'], 'Operations and support'), sm=(A['sm'], 'Sales and marketing'),
          ovh=(A['pd'] + A['ga'], 'Product development + General and administrative'), spec=(0.0, 'No such line in FY2024'), oi=(A['oi'], 'Income from operations'), where=FS,
          notes=dict(rev='Fees only. Host payouts are excluded.', direct='Merchant fees, chargebacks, hosting, software amortization. No property cost.', ops='Community support, refunds and credits, host protection. Includes stock pay.', sm='Includes field operations and policy, and stock pay.', ovh='Includes the stock pay booked in these two lines.'),
          memo=[('memo_stock_pay_all_lines', A['sbc'], 'Stock-based compensation expense', 'Note, Stock-Based Compensation', 'Already inside the cost lines above. Do not add.')])
block('Airbnb', 'per $100 of GBV', A['gbv'], LA)
LV = dict(rev=(Vv['rev'], 'Revenue'), direct=(Vv['cogs'], 'Cost of revenue, exclusive of depreciation and amortization shown separately below'), ops=(Vv['ops'], 'Operations and support'), sm=(Vv['sm'], 'Sales and marketing'),
          ovh=(Vv['tech'] + Vv['ga'] + Vv['dep'], 'Technology and development + General and administrative + Depreciation'), spec=(Vv['am'] + Vv['imp'], 'Amortization of intangible assets + Impairment of long-lived assets'), oi=(Vv['oi'], 'Loss from operations'), where=FS,
          notes=dict(rev='Includes Other services revenue that has no GBV behind it.', direct='Housekeeping, maintenance, payment fees, laundry, fixed rent on some contracts, residential management.', ops='Local operations staff and call centre.', sm='Includes payments to channel distribution partners and homeowner sales.', ovh='Includes stock pay in these lines.'),
          memo=[('memo_stock_pay_all_lines', Vv['sbc'], 'Equity-based compensation', 'Adjusted EBITDA reconciliation', 'Already inside the cost lines above.'),
                ('memo_other_services_revenue', Vv['other'], 'Other services', 'Note 6, Revenue', 'No GBV and no separate cost line. Removing the revenue alone gives a floor for left_after_direct_and_support.'),
                ('memo_restructuring_inside_lines', Vv['restr'], 'Restructuring', 'Adjusted EBITDA reconciliation', 'Already inside the cost lines above.')])
block('Vacasa', 'per $100 of GBV', Vv['gbv'], LV)


def sonder(basis, den, note):
    L = dict(rev=(S['rev'], 'Revenue'), direct=(S['cogs'], 'Cost of revenue (excluding depreciation and amortization)'), ops=(S['ops'], 'Operations and support'), sm=(S['sm'], 'Sales and marketing'),
             ovh=(S['ga'] + S['rd'], 'General and administrative + Research and development'), spec=(S['imp'] + S['integ'] + S['restr'], 'Impairment losses + Integration costs + Restructuring and other charges'), oi=(S['oi'], 'Loss from operations'), where=FS,
             notes=dict(rev=note, direct='Lease cost, cleaning and payment processing.', ops='Property-level costs, customer service, utilities and depreciation of property. D&A sits here and in R&D.', sm='Includes OTA service charges.', ovh='Includes stock pay in these lines.'),
             memo=[('memo_stock_pay_all_lines', S['sbc'], 'Stock-based compensation', 'Adjusted EBITDA reconciliation', 'Already inside the cost lines above. FY2023 was $28.5m.'),
                   ('memo_operating_lease_cost', S['lease'], 'Operating lease cost', 'Note, Leases', 'Already inside direct_costs.'),
                   ('memo_non_recurring_professional_fees', S['nrp'], 'Non-recurring professional fees', 'Adjusted EBITDA reconciliation', 'Already inside overhead. Marriott agreement and financing.'),
                   ('memo_dep_and_amortization', S['da'], 'Depreciation and amortization expense', 'Adjusted EBITDA reconciliation', 'Already inside operations and R&D.')])
    block('Sonder', basis, den, L)


sonder('per $100 of revenue', S['rev'], 'Reported. Sonder recognizes revenue net of taxes collected from guests, so this base excludes tax.')
for r in TAX:
    sonder(f'per $100 of estimated bookings, tax {r:.0%}', S['rev'] * (1 + r), f'Estimate: revenue x {1 + r:.2f}. Tax rate is a proxy, not a Sonder disclosure. OTA guest fees stay excluded.')
cols = list(rows[0])
with open(OUT + 'per100_peers.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)
pick = lambda co, b, it: next(r['per_100'] for r in rows if r['company'] == co and r['basis'].startswith(b) and r['line_item'] == it)
# gap split, Airbnb less Sonder on revenue
p = lambda x: x / S['rev'] * 100
ab = {k: pick('Airbnb', 'per', k) for k in ('left_after_direct_and_support', 'sales_and_marketing', 'overhead_and_stock_pay', 'operating_income_gaap')}
so = {k: pick('Sonder', 'per $100 of revenue', k) for k in ab}
gap = ab['operating_income_gaap'] - so['operating_income_gaap']
sp = []
def G(sec, item, val, note=''): sp.append(dict(section=sec, item=item, per_100=round(val, 2), share_of_gap=round(val / gap, 3) if sec == 'gap_airbnb_less_sonder' else '', note=note))
sec = 'gap_airbnb_less_sonder'
G(sec, 'property line: left after direct and support', ab['left_after_direct_and_support'] - so['left_after_direct_and_support'], 'Airbnb keeps 13.57 and Sonder 100, and both land near 9.7')
G(sec, 'sales and marketing', so['sales_and_marketing'] - ab['sales_and_marketing'], 'Model: Sonder rents demand from OTAs')
G(sec, 'non-recurring professional fees', p(S['nrp']), 'Rescue cost: Marriott agreement and financing')
G(sec, 'impairment, integration, restructuring', p(S['imp'] + S['integ'] + S['restr']), 'Rescue and exit cost. Impairment also recurred in FY2022 and FY2023.')
G(sec, 'VAT and bad debt increases', p(S['vat'] + S['bad']), 'Possible distress, year-on-year increases in G&A, cause not proven')
G(sec, 'remaining overhead gap', so['overhead_and_stock_pay'] - ab['overhead_and_stock_pay'] - p(S['nrp'] + S['vat'] + S['bad']), 'Scale: about $95m of G&A and R&D on $621m of revenue')
G(sec, 'total gap, GAAP operating income', gap, 'Sum of the lines above')
for lab, c in (('FY2023', dict(rev=602.066, cogs=392.898, ops=212.913, sm=78.566, ovh=112.082 + 22.365, spec=59.165 + 2.119, oi=-278.042)), ('FY2024', dict(rev=S['rev'], cogs=S['cogs'], ops=S['ops'], sm=S['sm'], ovh=S['ga'] + S['rd'], spec=S['imp'] + S['integ'] + S['restr'], oi=S['oi'])),
               ('H1 2024', dict(rev=298.080, cogs=195.015, ops=96.391, sm=40.821, ovh=53.557 + 9.064, spec=2.592, oi=-99.360)), ('H1 2025', dict(rev=265.941, cogs=177.824, ops=76.028, sm=33.029, ovh=33.557 + 7.801, spec=3.682 + 4.541, oi=-70.521))):
    assert abs(c['rev'] - c['cogs'] - c['ops'] - c['sm'] - c['ovh'] - c['spec'] - c['oi']) < .01, lab
    q = lambda x: x / c['rev'] * 100
    for it, val in (('direct costs', q(c['cogs'])), ('support and operations', q(c['ops'])), ('left after direct and support', q(c['rev'] - c['cogs'] - c['ops'])), ('sales and marketing', q(c['sm'])), ('overhead and stock pay', q(c['ovh'])), ('special lines', q(c['spec'])), ('operating income', q(c['oi']))):
        G('sonder_trend_per_100_revenue', f'{lab}: {it}', val, '10-K filed 24 Jul 2025' if lab.startswith('FY') else '10-Q filed 14 Oct 2025')
with open(OUT + 'per100_gap_split.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, list(sp[0])); w.writeheader(); w.writerows(sp)
order = ['revenue_kept', 'direct_costs', 'support_and_operations', 'left_after_direct_and_support', 'sales_and_marketing', 'left_after_sales_and_marketing', 'overhead_and_stock_pay', 'operating_income_before_special_lines', 'special_lines', 'operating_income_gaap']
print(f"{'':40}{'Airbnb':>9}{'Vacasa':>9}{'Son rev':>9}{'Son 14%':>9}{'10%':>8}{'20%':>8}")
for it in order:
    print(f"{it:40}{pick('Airbnb','per',it):9.2f}{pick('Vacasa','per',it):9.2f}{pick('Sonder','per $100 of revenue',it):9.2f}{pick('Sonder','per $100 of estimated bookings, tax 14',it):9.2f}{pick('Sonder','per $100 of estimated bookings, tax 10',it):8.2f}{pick('Sonder','per $100 of estimated bookings, tax 20',it):8.2f}")
print('dens',A['gbv'],Vv['gbv'],S['rev']); print({k:A[k] for k in ('sbc',)},Vv['sbc'],Vv['other'],Vv['restr'],S['sbc'],S['nrp'],S['da'],S['lease'],S['ebitda'],S['vat'],S['bad'])
print('vacasa floor',round((Vv['rev']-Vv['other']-Vv['cogs']-Vv['ops'])/Vv['gbv']*100,2),'vacasa platform rev',round((Vv['rev']-Vv['other'])/Vv['gbv']*100,2))
for r in sp: print(r['section'][:12],r['item'][:44].ljust(44),r['per_100'],r['share_of_gap'])
print(len(rows))
