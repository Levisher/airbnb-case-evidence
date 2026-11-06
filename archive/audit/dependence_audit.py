"""Score every row of the value chain dataset on the dependence standard agreed 6 Nov 2026.

T1 one named quantity: the cell and its basis give one numerator over one named base, in one unit.
T2 route shown: the row's own text carries the figures that reach the cell, or the cell is zero by definition.
T3 width named: any width in the cell comes from an assumption the row names.

Reads valuechain/companies.csv, changes nothing there, writes dependence_audit.csv beside this file.
source_type is the class of the first listed source other than Compustat, or third-party tracker when the basis uses KeyData.
The user's four classes are kept; trade press or broker is added because 13 rows fit none of them.
Every row-level decision that a text rule cannot make sits in AGREED, T2_FAIL, LINK_RECHECK, DROP or EDIT_ONLY.
"""
import csv, os, re, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'valuechain', 'companies.csv')
OUT = os.path.join(HERE, 'dependence_audit.csv')

# The user's decision of 6 Nov 2026. companies.csv still holds the old cell.
AGREED = {'Casago (owns Vacasa)': (
    'About 40% of Vacasa FY2024 GBV',
    'Vacasa 10-K: 70% of GBV through partners. KeyData Q2 2025: Airbnb 36 of 64 non-direct revenue points, 56.3%, so 39.4%; '
    'Q2 2026: 43 of 71, 60.6%, so 42.4%. Assumes the US partner mix. Each 10 points of partner mix moves the answer 7 points.')}

# Text passes the rule but another row contradicts it.
T2_FAIL = {'Tripadvisor': 'Zero asserted, while the trivago row says Airbnb buys little metasearch, so the same business is not shown at zero'}

# Links checked 6 Nov 2026 where the file says None found, Weak, or where a drop depends on it.
LINK_RECHECK = {
    'Twilio': 'Link is real but old. Twilio blog, 16 Sep 2011, Airbnb Voice Connect built on Twilio. Twilio customer page now redirects with no Airbnb text. Current status unconfirmed',
    'Adyen': 'Link is real but old. Bloomberg, 1 Sep 2016, describes Adyen processing an Airbnb payment. Current status unconfirmed',
    'Teleperformance': 'Search summary pointed to a Tokyo job listing. The fetched page shows neither Airbnb nor Teleperformance, so unconfirmed',
    'Concentrix': 'Search found no Airbnb link',
    'TaskUs': 'Search found no Airbnb link',
    'TTEC': 'Search found no Airbnb link',
}

# rule code: A no evidenced link, B one weak lead, C not paid when a home is rented, D no longer operating
DROP = {
    'Sonder': ('D', 'Wound down Nov 2025, so it earns nothing from a rental today. Keep its 2024 figures as a historical comparison'),
    'Inspirato': ('A', 'No confirmed distribution through Airbnb, and own subscribers fill the homes'),
    'Pacaso': ('A', 'No Airbnb link found, and owners use the homes, so rental is outside the model'),
    'First Advantage': ('A', 'No public Airbnb link, and Airbnb does not name its check vendor'),
    'Concentrix': ('A', 'No evidence of an Airbnb contract. A ceiling on an unproven link adds nothing'),
    'TaskUs': ('A', 'No evidence of an Airbnb contract. A ceiling on an unproven link adds nothing'),
    'TTEC': ('A', 'No evidence of an Airbnb contract. A ceiling on an unproven link adds nothing'),
    'Teleperformance': ('A', 'No confirmed Airbnb contract. Fold into one group row for outsourced support, vendors unnamed'),
    'TELUS Digital': ('B', 'One unconfirmed host forum post. Fold into one group row for outsourced support, vendors unnamed'),
    'Similarweb': ('C', 'Sells traffic estimates to third parties, so no money moves when a home is rented'),
    'Allegion (Schlage)': ('C', 'One-off hardware sale with no Airbnb contract, and the short-let end market is undisclosed'),
    'ASSA ABLOY (Yale, August)': ('C', 'One-off hardware sale with no Airbnb contract, and the short-let end market is undisclosed'),
    'Granicus (Host Compliance)': ('C', 'Cities pay it to enforce rental rules. Belongs in the regulation section'),
    'AU10TIX': ('C', 'Airbnb is not a stated client, and the Guesty link sits inside the Guesty row'),
}

# Failing rows whose fix needs no new evidence, with the corrected cell.
EDIT_ONLY = {
    'Amazon (AWS)': 'Below 0.1% of Amazon revenue if Airbnb spends under $717m a year on AWS. $219m is the 2026 purchase obligation, a minimum',
    'Meta': 'Below 0.8% of Meta revenue, $1,595m of all marketing over $200,966m',
    'Visa': 'Below 4.5% of Visa revenue, all $2,086m of Airbnb 2025 cost of revenue over $45,903m. The filed 0.5% needs Visa below $230m, which no source shows, and the $1.67bn fee bill was not found in the 10-K text',
    'Mastercard': 'Below 6.4% of Mastercard revenue, all $2,086m of Airbnb 2025 cost of revenue over $32,791m. The filed 0.5% needs Mastercard below $164m, which no source shows',
    'PayPal (Braintree, Hyperwallet)': 'Below 6.3% of PayPal revenue, all $2,086m of Airbnb 2025 cost of revenue over $33,172m. The filed 0.5% needs PayPal below $166m, which no source shows',
    'Generali': 'Not disclosed',
    'Marriott (Homes & Villas)': 'Not applicable, rival. Move to the rival layer',
    'Hilton': 'Not applicable, rival. Move to the rival layer',
    'Accor (onefinestay)': 'Not applicable, rival. Move to the rival layer',
    'OpenAI (ChatGPT)': 'Not applicable, rival. No booking flows today',
}

FILING = re.compile(r'10-K|filings|release|report|\bcalls?\b|letter|Compustat', re.I)
TRACKER = re.compile(r'KeyData|RedAwning|Inside Airbnb census|Multiples\.vc|Clay|CB Insights|eMarketer', re.I)
FORUM = re.compile(r'r/airbnb|community forum|Capterra|\bG2\b|Software Advice|[Vv]endor reviews', re.I)
VENDOR = re.compile(r'[Vv]endor pages|blog|\bsite\b|pricing page|help pages|proper\.insure|newsroom|Businesswire|press release|^Granicus|^Holidu|^Key Data', re.I)


def src_class(tok):
    # Vendor test runs before the filing test, because vendor reports and blogs share words with filings.
    if TRACKER.search(tok) and not tok.startswith('Key Data'): return 'third-party tracker'
    if FORUM.search(tok): return 'forum'
    if re.search(r'Rentals United and PriceLabs report', tok): return 'vendor page'
    if VENDOR.search(tok): return 'vendor page'
    if FILING.search(tok): return 'filing'
    return 'trade press or broker'


def cell_class(c):
    if c.startswith('0%'): return 'point'
    if re.match(r'(Below|Up to)\b', c): return 'bound'
    if re.match(r'\d+% to \d+%', c): return 'range'
    if c.startswith('About'): return 'point'
    if c.startswith('Indirect ('): return 'market band'
    if c in ('Unknown', 'Not disclosed', 'Indirect') or c.startswith('Indirect, opposite'): return 'no estimate'
    return 'ordinal'


def figures(t):
    return re.findall(r'\$[\d,.]+\s?(?:bn|m)?|\d+(?:\.\d+)?%', t)


BASE = re.compile(r'of (?:\d{4} )?(?:group )?revenue|group revenue|premium base|against \$|No revenue through Airbnb|of Vacasa FY2024 GBV', re.I)
KEY = re.compile(r'KeyData|US managed|US managers', re.I)


def score(cell, basis, company, agreed=True):
    k = cell_class(cell)
    agreed = agreed and company in AGREED
    market = bool(KEY.search(basis)) and not agreed
    both_units = bool(re.search(r'revenue', basis) and re.search(r'reservations', basis))
    # T1
    if k in ('ordinal', 'no estimate'):
        t1, r1 = False, 'Label with no numerator or base' if k == 'ordinal' else 'States that no estimate exists'
    elif k == 'market band':
        t1, r1 = False, 'US market band in two units, attached to a firm'
    elif k == 'range' and (both_units or market):
        t1, r1 = False, 'Two measures of a market figure, revenue and reservations'
    elif k == 'range':
        t1, r1 = False, 'Two denominators in one range'
    elif not BASE.search(cell + ' ' + basis):
        t1, r1 = False, 'Number given with no base named'
    else:
        t1, r1 = True, 'One numerator over a named base'
    # T2
    defined = cell.startswith('0%') and 'No revenue through Airbnb' in basis
    if company in T2_FAIL:
        t2, r2 = False, T2_FAIL[company]
    elif defined:
        t2, r2 = True, 'Zero by definition, a rival sells its own inventory'
    elif market:
        t2, r2 = False, 'Market average applied with no firm data'
    elif not t1:
        t2, r2 = False, 'No route without a named base'
    elif len(figures(basis)) >= 2:
        t2, r2 = True, 'Figures in the row reach the cell'
    else:
        t2, r2 = False, 'Fewer than two figures, so the cell cannot be reached from the row'
    # T3
    vac = 'no'
    if agreed:
        t3, r3 = True, 'Partner mix is the named assumption, with a stated sensitivity'
    elif k == 'point':
        t3, r3 = True, 'Point value, no width'
    elif k == 'bound':
        t3 = bool(re.search(r'ceiling', basis, re.I))
        r3 = 'Ceiling assumption is named' if t3 else 'Bound rests on no named assumption'
    elif k == 'no estimate' and not market:
        t3, r3, vac = True, 'Claims no width', 'yes'
    elif k == 'no estimate':
        t3, r3 = False, 'Cell is silent, and the basis carries the 43% to 51% band'
    else:
        t3, r3 = False, 'Implied width with no named assumption'
    return k, t1, r1, t2, r2, t3, r3, vac


def main():
    rows = list(csv.DictReader(open(SRC, encoding='utf-8')))
    print('company rows', len(rows))
    out = []
    for r in rows:
        co, filed, basis = r['Company'], r['Estimated dependence on Airbnb'], r['Basis for the estimate']
        cell, b = AGREED.get(co, (filed, basis))
        if b.startswith('As '):  # 'As Visa' inherits the named row's basis
            b = next(x['Basis for the estimate'] for x in rows if x['Company'].startswith(b[3:].strip()))
            basis = b
        k, t1, r1, t2, r2, t3, r3, vac = score(cell, b, co)
        fk, f1, _, f2, _, f3, _, _ = score(filed, basis, co, agreed=False)
        toks = [t.strip() for t in r['Sources'].split(';') if t.strip()]
        classes = [src_class(t) for t in toks]
        keydata = bool(KEY.search(b))
        named = [c for t, c in zip(toks, classes) if not t.startswith('Compustat')] or classes
        stype = 'third-party tracker' if keydata else named[0]
        if k == 'no estimate' or (k == 'ordinal' and not keydata):
            rests = 'no estimate' if k == 'no estimate' else 'judgement'
        elif keydata and co not in AGREED:
            rests = 'market figure transferred'
        elif t2 and cell.startswith('0%'):
            rests = 'definition'
        else:
            rests = 'sourced figure' if len(figures(b)) >= 1 else 'judgement'
        fails = [n for n, ok in (('T1', t1), ('T2', t2), ('T3', t3)) if not ok]
        if co in DROP:
            action, why = 'drop', DROP[co][0] + '. ' + DROP[co][1]
        elif not fails:
            action = 'keep'
            why = 'Rival, show as not applicable' if k == 'point' and cell.startswith('0%') else 'Meets the standard'
        elif co in EDIT_ONLY:
            action, why = 'edit only', EDIT_ONLY[co]
        else:
            action, why = 'needs evidence', 'Needs a firm-level figure or a filing check before any number stands'
        out.append({
            'layer': r['Layer'], 'company': co, 'position': r['Position in the chain'],
            'dependence_as_filed': filed, 'dependence_scored': cell, 'cell_class': k,
            't1_one_named_quantity': 'pass' if t1 else 'fail', 't1_reason': r1,
            't2_route_shown': 'pass' if t2 else 'fail', 't2_reason': r2,
            't3_width_named': 'pass' if t3 else 'fail', 't3_reason': r3, 't3_vacuous': vac,
            'tests_failed': len(fails), 'row_result': 'fail' if fails else 'pass',
            'row_result_as_filed': 'pass' if (f1 and f2 and f3) else 'fail',
            'source_type': stype, 'estimate_rests_on': rests,
            'second_hand_source': 'yes' if keydata else 'no',
            'estimate_source_in_sources_column': ('yes' if re.search('KeyData|RedAwning', r['Sources']) else 'no') if keydata else 'n/a',
            'source_types_listed': '; '.join(sorted(set(classes))), 'sources': r['Sources'],
            'evidence_as_filed': r['Evidence for the relationship'], 'confidence_as_filed': r['Confidence'],
            'link_recheck_6nov2026': LINK_RECHECK.get(co, ''), 'action': action, 'action_reason': why})
    # Every drop must rest on something the file itself records.
    for co, (code, _) in DROP.items():
        r = next(x for x in rows if x['Company'] == co)
        ok = (r['Evidence for the relationship'] in ('None found', 'Weak') or 'Defunct' in r['Public or private status']
              or r['Position in the chain'] == 'Rule-maker' or 'one step removed' in r['Relationship with Airbnb'])
        assert ok, co
    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    n = len(out); bad = [o for o in out if o['row_result'] == 'fail']
    print('fail', len(bad), 'of', n, '| as filed fail', sum(o['row_result_as_filed'] == 'fail' for o in out))
    for t in ('t1_one_named_quantity', 't2_route_shown', 't3_width_named'):
        print(t, 'fail', sum(o[t] == 'fail' for o in out))
    print('vacuous T3', sum(o['t3_vacuous'] == 'yes' for o in out))
    g = defaultdict(list)
    for o in out: g[o['layer']].append(o)
    print('layer | rows | fail | rate | mean tests failed')
    for l, v in sorted(g.items(), key=lambda kv: (-sum(x['row_result'] == 'fail' for x in kv[1]) / len(kv[1]), -sum(x['tests_failed'] for x in kv[1]) / len(kv[1]))):
        fl = sum(x['row_result'] == 'fail' for x in v)
        print(f"{l} | {len(v)} | {fl} | {fl / len(v):.0%} | {sum(x['tests_failed'] for x in v) / len(v):.2f}")
    for key in ('action', 'source_type', 'estimate_rests_on', 'cell_class'):
        print(key, Counter(o[key] for o in out).most_common())
    print('source_type x result', sorted(Counter((o['source_type'], o['row_result']) for o in out).items()))
    print('rests x result', sorted(Counter((o['estimate_rests_on'], o['row_result']) for o in out).items()))
    print('pass', [o['company'] for o in out if o['row_result'] == 'pass'])
    print('KeyData not in Sources', sum(o['estimate_source_in_sources_column'] == 'no' for o in out))


if __name__ == '__main__':
    main()
