"""Audit of the 54-task host map. Builds task_map_audit.csv from the filed map and the checks below.

Coding rules, written before any row was entered here, after reading the filed map and the first stage answers.
The scoring is therefore unblinded and single-coder.

Airbnb role. Filed labels map to the note's split as: Owns* = Done (21), Partial/Offers/Tool/Partner/Pilot = Partly (16),
None = No role (17).
  Done    a shipped Airbnb product or policy completes the task by default on Airbnb bookings in its main markets,
          or Airbnb alone makes the deciding act. The host adds set-up or evidence only.
  Partly  a shipped product covers a named part of the task, or the task needs host work each time, or the product
          is opt-in, in pilot, rolling out, or limited by market or portfolio size.
  No role no shipped Airbnb product performs any part of the task. A discount on someone else's product is no role.

Automation rating.
  High    a shipped tool completes the task with no person per occurrence after set-up.
  Medium  software does part, and a person is needed each time.
  Low     a person on site or a professional is needed each time, and software at most schedules it.

Verdicts. Survives = a named outside source is consistent with the filed rating. Fails = a named source puts the task
in a different level. No usable check = nothing found, or the source cannot separate the levels. A rating with no usable
check is counted neither as survived nor as failed.
"""
import csv, os, sys, collections
sys.path.insert(0, os.path.expanduser('~/Downloads/ABNB/valuechain/_scripts'))
from activities import A

OUT = os.path.expanduser('~/Downloads/ABNB/audit/task_map_audit.csv')
S, F, N = 'Survives', 'Fails', 'No usable check'
H, M, L = 'High', 'Medium', 'Low'
D, P, X = 'Done', 'Partly', 'No role'
VP, FI, HF, AH, TP, AC = 'Vendor page', 'Filing', 'Host forum', 'Airbnb page', 'Trade press', 'Airbnb call'

def bucket(s):
    k = s.split(':')[0].strip()
    if k.startswith('Owns'): return D
    if k == 'None': return X
    return P

# task_no: automation (finding, source, type, verdict, corrected),
#          role (finding, source, type, verdict, corrected, failure kind, source interest)
C = {}
def c(n, af, asrc, at, av, ac, rf, rsrc, rt, rv, rc, kind='', interest=''):
    C[n] = (af, asrc, at, av, ac, rf, rsrc, rt, rv, rc, kind, interest)

c(1, 'Airbtics sells property-level data at $295 a month and Awning runs a free calculator, so a tool produces the estimate unaided',
  'r/ShortTermRentals 2025-07-30; Awning calculator page', HF, S, H,
  'Airbnb estimates earnings for an address from 12 months of similar listings. The map\'s own how-column cites this estimator while the role reads None',
  'Airbnb help article 4145', AH, F, P, 'Coded against Airbnb', 'Airbtics post is promotional')
c(2, 'A compliance manager does licences, permits and zoning by hand. No lookup tool found, so Medium and Low cannot be separated',
  'r/vrbo 2025-09-29', HF, N, M,
  'Airbnb publishes guidance under Hosting responsibly and its estimator warns that hosting may depend on local law. Guidance covers part of the check',
  'Airbnb site footer; Airbnb help article 4145', AH, S, P)
c(3, 'Host bought the property personally', 'r/airbnb_hosts 2026-06-11', HF, S, L,
  'Airbnb-friendly apartments launched November 2022 with Greystar in 175 buildings and is still listed on the site',
  'Airbnb Q4 2022 call; Airbnb site footer', AC, S, P)
c(4, 'No forum quote and no lender page checked', 'None found', '', N, M,
  'Financial help appears only as a host wish in the September 2025 talk', 'Airbnb conference talk, Sep 2025', AC, S, X)
c(5, 'Host did the design and bought the furniture by hand', 'r/airbnb_hosts 2026-03-28', HF, S, L,
  'No Airbnb product in calls or filings', 'Airbnb calls Q3 2022 to Q2 2026', AC, S, X)
c(6, 'Airbnb\'s integration generates a unique door code for each stay automatically', 'Airbnb newsroom, smart lock integrations', AH, S, H,
  'Shipped to all US and Canada hosts for Schlage, August and Yale. Other markets and brands sit outside it',
  'Airbnb newsroom, smart lock integrations', AH, S, P)
c(7, 'NoiseAware sells monitoring at $15 a month and Minut from $5 plus a sensor, and alerts run unattended', 'Houfy noise monitor comparison, vendor prices Oct 2026', VP, S, H,
  'The filed role is a discount on third-party devices. Airbnb\'s product performs no part of the task',
  'Rental Scale-Up, party prevention article', TP, F, X, 'Definition', 'Rental Scale-Up is a PriceLabs site')
c(8, 'RentPermit tracks expiry dates and night caps, and hosts still file renewals by hand', 'r/vrbo 2026-02-26', HF, S, M,
  'Hosts add a registration number or exemption on Airbnb. Permit filing stays with the host', 'Airbnb help article 2038', AH, S, P)
c(9, 'Avalara MyLodgeTax sells registration and filing as a service', 'Avalara occupancy tax guide', VP, S, H,
  'Airbnb collects in listed jurisdictions only. Avalara quotes Airbnb that taxes it does not collect are the host\'s responsibility, and the task here is registration',
  'Avalara occupancy tax guide; r/airbnb_hosts 2026-09-17', VP, F, P, 'Fact', 'Avalara sells the alternative')
c(10, 'Proper sells policies and AirCover applies to every Airbnb stay, while claims need a person', 'r/airbnb_hosts 2026-07-22', HF, S, M,
  'The label says Owns part and the split counted it as Done. Cover is $3m and $1m per the 10-K, applies to Airbnb stays only, and a host in July 2026 was shopping for Proper',
  'Airbnb 10-K Feb 2026; Hostfully AirCover guide; r/airbnb_hosts 2026-07-22', FI, F, P, 'Fact', 'Hostfully sells software to hosts')
c(11, 'Host buys and configures a $30 Roku in guest mode', 'r/airbnb_hosts 2025-11-03', HF, S, L,
  'No Airbnb product in calls or filings', 'Airbnb calls Q3 2022 to Q2 2026', AC, S, X)
c(12, 'Turno alerts on low stock by property and can require cleaners to log inventory. A person still counts and fills',
  'Turno inventory management page', VP, S, M,
  'House restocking appears only as a host wish', 'Airbnb conference talk, Sep 2025', AC, S, X)
c(13, 'Airbnb\'s model sorts photos by room and a photographer still attends', 'Airbnb Q1 2024 call', AC, S, M,
  'Airbnb runs a paid photo programme, charged against future payouts and subject to a nearby photographer. One host paid outside it',
  'Airbnb professional photography page; r/airbnb_hosts 2026-03-28', AH, S, P)
c(14, 'Smart Setup builds a listing from photos and an address', 'Rental Scale-Up, Summer 2026 release', TP, S, H,
  'Smart Setup covers new listings, in the US since summer 2026 and elsewhere from early 2027. The map itself says rolling out',
  'Rental Scale-Up, Fall 2026 update', TP, F, P, 'Fact', 'Rental Scale-Up is a PriceLabs site')
c(15, 'PriceLabs sets rates at $14.49 per listing a month after a 27% cut in April 2026', 'PricingSaaS, PriceLabs history', VP, S, H,
  'Smart Pricing is opt-in and prices Airbnb listings only. One host measured it 27% below PriceLabs and kept paying for PriceLabs',
  'Rental Scale-Up, Fall 2026 update; r/airbnb_hosts 2026-10-11', HF, F, P, 'Fact', 'Rental Scale-Up is a PriceLabs site')
c(16, 'A $30 a month tool syncs calendars, photos and prices from one place', 'r/airbnb_hosts 2026-09-17', HF, S, H,
  'Airbnb ships the Host API that every channel manager connects to, and an exported iCal feed. It offers no outbound syndication, so it covers one side of the sync',
  'Airbnb Q1 2026 call; r/airbnb_hosts 2026-10-23', AC, F, P, 'Coded against Airbnb')
c(17, 'A PMS at $15 to $30 a listing connects Stripe for direct bookings', 'r/airbnb_hosts 2026-10-24', HF, S, H,
  'Invited hosts get a link at 6% or 10%, with no help article or published terms found, and the booking stays on Airbnb',
  'Rental Scale-Up, direct booking links; Houfy, pilot review', TP, S, P, '', 'Rental Scale-Up is a PriceLabs site, Houfy is a rival')
c(18, 'Hosts set promotions by hand and the ranking itself runs unattended', 'r/airbnb_hosts 2026-05-13', HF, S, M,
  'Airbnb runs the ranking. The task as filed is performed by the owner or co-host, who sets discounts by hand, and paid placement is only described',
  'Airbnb Q4 2024 call; r/airbnb_hosts 2026-05-13', AC, F, P, 'Definition')
c(19, 'Hospitable pushes blocks to Vrbo and Airbnb daily with no person', 'r/airbnb_hosts 2026-10-23', HF, S, H,
  'The calendar shipped to all hosts, but a host on two channels runs it from a channel manager. The map\'s own how-column says only for single-channel hosts',
  'Airbnb Q2 2025 call; r/airbnb_hosts 2026-10-23', HF, F, P, 'Definition')
c(20, 'PriceLabs, Wheelhouse and Beyond push rates unattended', 'r/airbnb_hosts 2025-08-20', HF, S, H,
  'The new tool went to opted-in hosts in October 2026 and the model was still rolling out in August. Hosts pay PriceLabs for the same work',
  'Rental Scale-Up, Fall 2026 update; Airbnb Q2 2026 call; r/airbnb_hosts 2025-08-20', AC, F, P, 'Fact', 'Rental Scale-Up is a PriceLabs site')
c(21, 'Hospitable and Host Tools auto-reply to guest messages', 'Hospitable and Host Tools help pages', VP, S, H,
  'Quick replies are templates the host sends. Ask about this home answers without the host, before booking only',
  'Airbnb help article 2898; Rental Scale-Up, Summer 2026 release', AH, F, P, 'Definition', 'Rental Scale-Up is a PriceLabs site')
c(22, 'Truvi charges per booking and Autohost per verification, both automated', 'Truvi pricing page', VP, S, H,
  'Every booker must hold a verified ID, and reservation screening is shipped. The Autohost quote concerns a Vrbo booking',
  'Airbnb Q1 2026 call; Airbnb 10-K Feb 2026; r/airbnb_hosts 2025-07-20', FI, S, D)
c(23, 'Airbnb collects at checkout and pays out after check-in with no host action', 'r/AirBnBHosts 2025-09-02', HF, S, H,
  'Airbnb is merchant of record and bears payment processing costs', 'Airbnb 10-K Feb 2026', FI, S, D)
c(24, 'Airbnb computes and remits tax at booking', 'r/AirBnB 2026-10-05', HF, S, H,
  'Default where Airbnb has an agreement. Hosts still collect elsewhere, and a host puts it at most locations',
  'Avalara occupancy tax guide; r/airbnb_hosts 2026-09-17', HF, S, D)
c(25, 'Airbnb sends scheduled replies on triggers, and a PMS auto-messages all channels', 'Airbnb help article 2897; r/airbnb_hosts 2025-12-30', AH, S, H,
  'Scheduled quick replies send automatically on new reservation, check-in or checkout once the host writes the template. Set-up only, so Done holds',
  'Airbnb help article 2897', AH, S, D)
c(26, 'Airbnb supplies the door code where a lock is linked, and a lockout still reaches a support agent',
  'r/AirBnB 2026-10-15; Airbnb conference talk, Sep 2026', HF, S, M,
  'Check-in instructions are a shipped field and AI advises agents on lockouts. Access problems at the door stay with the host or co-host',
  'Airbnb help article 2897; Airbnb conference talk, Sep 2026', AH, S, P)
c(27, 'Hospitable auto-replies, and Breezeway added a Concierge AI messaging add-on in August 2026. Hosts without them answer by hand',
  'Hospitable help pages; PricingSaaS, Breezeway Aug 2026; r/airbnb_hosts 2025-10-24', VP, S, H,
  'AI quick replies help the host answer and an AI assistant serves guests. The host still answers in-stay questions',
  'Airbnb Q1 2024 call; r/airbnb_hosts 2025-10-24', AC, S, P)
c(28, 'A host keeps an emergency number that always rings, so a person responds', 'r/airbnb_hosts 2025-10-12', HF, S, L,
  'The 10-K lists an urgent safety line. On-site response stays with the host', 'Airbnb 10-K Feb 2026', FI, S, P)
c(29, 'Sensors and cameras alert automatically and a person then acts', 'r/airbnb_hosts 2026-06-11; Houfy noise monitor comparison', HF, S, M,
  'Reservation screening and the party ban act at booking. During the stay hosts use their own cameras and paid sensors, and neighbours call a support line',
  'Airbnb Q4 2022 call; Airbnb 10-K Feb 2026; r/airbnb_hosts 2026-06-11', FI, F, P, 'Fact')
c(30, 'HostAI proposes upsells from the calendar and Hospitable offers early check-in automatically', 'Hostaway marketplace, HostAI; Hospitable upsells page', VP, S, H,
  'Airbnb sells its own add-ons to guests. No product exists for host-sold upsells, and a host charged late checkout by hand through the app',
  'Rental Scale-Up, Fall 2026 update; r/airbnb_hosts 2026-03-17', HF, F, P, 'Fact', 'Rental Scale-Up is a PriceLabs site')

c(31, 'Breezeway creates cleaning tasks when a reservation is confirmed, and Turno sells scheduling at $10 a property a month', 'Turno help, subscription plans; Breezeway via search listing', VP, S, H,
  'No Airbnb product in calls or filings', 'Airbnb calls Q3 2022 to Q2 2026', AC, S, X)
c(32, 'Hosts pay cleaners per visit', 'r/vrbo 2026-10-27', HF, S, L,
  'A cleaning marketplace is only described. The Co-Host Network matches people who may contract cleaners, which is row 54', 'Airbnb conference talk, Sep 2025; Airbnb co-host page', AC, S, X)
c(33, 'A host recommends a pick-up and drop-off laundry service', 'r/airbnb_hosts 2026-10-27', HF, S, L,
  'No Airbnb product in calls or filings', 'Airbnb calls Q3 2022 to Q2 2026', AC, S, X)
c(34, 'A host refills dispensers at each turnover. Turno alerts on low stock, which only triggers the visit, so the rule puts this at Low', 'r/airbnb_hosts 2025-09-22; Turno inventory management page', HF, F, L,
  'Restocking appears only as a host wish', 'Airbnb conference talk, Sep 2025', AC, S, X)
c(35, 'Breezeway requires photo checklists and RapidEye and CleanQA grade the photos, and a person still takes them', 'RapidEye and CleanQA vendor pages via search listing', VP, S, M,
  'Verified photos cover listing set-up. No turnover inspection product exists', 'Airbnb conference talk, Sep 2025', AC, S, X)
c(36, 'Local garbage removal is paid for and a host manages the hot tub personally', 'r/vrbo 2026-10-26', HF, S, L,
  'No Airbnb product in calls or filings', 'Airbnb calls Q3 2022 to Q2 2026', AC, S, X)
c(37, 'Ezcare and Lodgify schedule recurring jobs, and the work itself needs a person', 'Ezcare maintenance software page; Lodgify preventive maintenance entry', VP, S, L,
  'No Airbnb product in calls or filings', 'Airbnb calls Q3 2022 to Q2 2026', AC, S, X)
c(38, 'A manager quoted $90 for a handyman and the host fixed the seat personally', 'r/AirBnBHosts 2026-06-25', HF, S, L,
  'Service help is only described in the September 2025 talk', 'Airbnb conference talk, Sep 2025', AC, S, X)
c(39, 'Orkin attended in person after the host agreed', 'r/AirBnB 2026-10-16', HF, S, L,
  'Support pressed the host to act. No Airbnb product does the work', 'r/AirBnB 2026-10-16', HF, S, X)
c(40, 'A host replaced linens and pillows personally at $1,000', 'r/airbnb_hosts 2026-07-09', HF, S, L,
  'No Airbnb product in calls or filings', 'Airbnb calls Q3 2022 to Q2 2026', AC, S, X)
c(41, 'ProhostAI drafts the guest review and submits it on a chosen day', 'ProhostAI auto-reviews guide', VP, S, H,
  'Airbnb owns the two-sided system, and hosts write the review themselves', 'Airbnb Q1 2024 call; r/airbnb_hosts 2026-08-26', AC, F, P, 'Definition')
c(42, 'Hostaway describes tools that publish replies unattended. Hospitable only suggests a reply and the host sends it', 'Hostaway glossary, automated review response; Hospitable help article 9257136', VP, S, H,
  'Filed as owning the feed. The host writes the reply, and no Airbnb reply tool appears in calls', 'r/AirBnB 2026-10-05; Hospitable help article 9257136', HF, F, P, 'Definition')
c(43, 'Hosts file by hand with evidence, and a Hospitable request for automated disputes shows no such tool there. Medium and Low cannot be separated', 'Hostfully review removal guide; Hospitable feature board', VP, N, M,
  'Only Airbnb can remove a review, with two requests allowed per review. A host reports one removed', 'Hostfully review removal guide; r/airbnb_hosts 2026-10-18', VP, S, D, '', 'Hostfully sells software to hosts')
c(44, 'A person assembles evidence and files within deadlines', 'RedAwning AirCover claims guide', VP, S, M,
  'Airbnb decides and pays under AirCover. The host supplies evidence only', 'Airbnb 10-K Feb 2026; r/airbnb_hosts 2025-07-22', FI, S, D, '', 'RedAwning distributes rival channels')
c(45, 'AI handling of rebooking was described in 2024 as a later phase, so people still handle part', 'Airbnb Q3 2024 call', AC, S, M,
  'AirCover for guests and the rebooking guarantee are shipped and sit with Airbnb', 'Airbnb 10-K Feb 2026; Airbnb conference talk, Sep 2022', FI, S, D)
c(46, 'No source says how far dispute handling is automated', 'None found', '', N, H,
  'Airbnb is merchant of record and booked $67m of chargeback expense in 2025', 'Airbnb 10-K Feb 2026', FI, S, D)
c(47, 'A host paid to post a laptop back, and Turno says hosts handle all communication. A person handles the item each time, so the rule puts this at Low', 'r/ShortTermRentals 2026-01-13; Turno lost item guide', HF, F, L,
  'Messaging carries the conversation and no lost-property product exists. Borderline, kept as filed', 'Turno lost item guide', VP, S, P, '', 'Turno sells to hosts')
c(48, 'Guesty matches transactions with AI and groups Airbnb payouts into daily batches', 'Guesty accounting page', VP, S, H,
  'The earnings page exports transactions as CSV. Matching batches to bookings stays with the host or software', 'r/airbnb_hosts 2026-10-27; VRPlatform reconciliation guide', HF, S, P)
c(49, 'Guesty produces customisable owner statements', 'Guesty accounting page', VP, S, H,
  'Airbnb splits payouts with co-hosts and issues no owner statement. Borderline, kept as filed', 'Airbnb help article 3389; r/airbnb_hosts 2026-08-25', AH, S, P)
c(50, 'Airbnb supplies the 1099-K and a CSV, and a host still files personally', 'Airbnb help article 414; r/airbnb_hosts 2026-10-12', AH, S, M,
  'Tax forms ship. Filing help is only a host wish', 'Airbnb help article 414; Airbnb conference talk, Sep 2025', AH, S, P)
c(51, 'RentPermit tracks expiry, and a host found out by email two weeks before expiry and renewed by hand', 'r/vrbo 2026-02-26; r/vrbo 2026-07-08', HF, S, M,
  'Licence help is only described', 'Airbnb conference talk, Sep 2025', AC, S, X)
c(52, 'Hosts manage neighbours personally', 'r/airbnb_hosts 2026-06-11', HF, S, L,
  'The 10-K lists a 24/7 neighbourhood support line, and neighbours report through it', 'Airbnb 10-K Feb 2026; Airbnb help article 3290', FI, S, P)
c(53, 'PriceLabs sells market dashboards at $9.99 a month', 'PricingSaaS, PriceLabs history', VP, S, H,
  'The AI earnings dashboard serves hosts with five or fewer listings, while portfolios of six or more get a calendar. Portfolio reporting stays with Key Data and AirDNA',
  'Rental Scale-Up, Fall 2026 update; Airbnb Q1 and Q2 2026 calls', TP, F, P, 'Fact', 'Rental Scale-Up is a PriceLabs site')
c(54, 'Managers quote 15% to 17% for people-run service. The row bundles the other tasks', 'r/airbnb_hosts 2026-06-04', HF, S, M,
  'The Co-Host Network matches hosts to co-hosts in ten countries. The no added fee wording in the map was not confirmed', 'Airbnb co-host page', AH, S, P)

# BUILD
ARRIVED = lambda k: os.path.isfile(os.path.expanduser(f'~/Downloads/ABNB/audit/task_map_ev/{k}.json'))
KEY = {'Acquire and qualify': 'acquire', 'Set up and comply': 'set', 'List and sell': 'list', 'Book and communicate': 'book',
       'Stay support': 'stay', 'Turnover': 'turnover', 'Maintain': 'maintain', 'After the stay': 'after', 'Run the business': 'run'}
UNV = 'Unverified'
COLS = ['task_no', 'stage', 'task', 'who_performs', 'automation_rating', 'automation_outside_check', 'automation_source',
        'automation_source_type', 'automation_verdict', 'automation_corrected', 'airbnb_role_as_filed', 'role_bucket_as_filed',
        'role_outside_check', 'role_source', 'role_source_type', 'role_verdict', 'role_bucket_corrected', 'failure_kind',
        'source_interest', 'stage_answer_arrived']
rows = []
for i, r in enumerate(A, 1):
    k = KEY[r[0]]
    arr = ARRIVED('host_' + k) and ARRIVED('abnb_' + k)
    b = bucket(r[7])
    if i in C:
        af, asrc, at, av, ac, rf, rsrc, rt, rv, rc, kind, it = C[i]
    else:
        af = rf = 'Stage answer did not arrive, so no check was made'
        asrc = rsrc = at = rt = kind = it = ''
        av = rv = UNV; ac = r[6]; rc = b
    rows.append(dict(zip(COLS, [i, r[0], r[1], r[2], r[6], af, asrc, at, av, ac, r[7], b, rf, rsrc, rt, rv, rc, kind, it, 'Yes' if arr else 'No'])))
with open(OUT, 'w', newline='') as f:
    w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(rows)

LV = {D: 2, P: 1, X: 0}
print('automation', collections.Counter(x['automation_verdict'] for x in rows))
print('role', collections.Counter(x['role_verdict'] for x in rows))
print('both survive', sum(x['automation_verdict'] == S and x['role_verdict'] == S for x in rows))
print('filed', collections.Counter(x['role_bucket_as_filed'] for x in rows))
print('corrected', collections.Counter(x['role_bucket_corrected'] for x in rows))
len_ = {x['task_no']: x['role_bucket_as_filed'] if x['failure_kind'] == 'Definition' else x['role_bucket_corrected'] for x in rows}
print('lenient', collections.Counter(len_.values()))
print('moves', collections.Counter((x['role_bucket_as_filed'], x['role_bucket_corrected']) for x in rows if x['role_verdict'] == F))
print('kinds', collections.Counter(x['failure_kind'] for x in rows if x['role_verdict'] == F))
print('stage | n | checked | down | up | net per checked | filed done | corrected done | lenient net')
for s in KEY:
    g = [x for x in rows if x['stage'] == s]; ck = [x for x in g if x['role_verdict'] != UNV]
    dn = sum(LV[x['role_bucket_as_filed']] > LV[x['role_bucket_corrected']] for x in ck)
    up = sum(LV[x['role_bucket_as_filed']] < LV[x['role_bucket_corrected']] for x in ck)
    ln = sum(LV[x['role_bucket_as_filed']] - LV[len_[x['task_no']]] for x in ck)
    print(s, len(g), len(ck), dn, up, round((dn - up) / len(ck), 3) if ck else None,
          sum(x['role_bucket_as_filed'] == D for x in g), sum(x['role_bucket_corrected'] == D for x in g), ln)

named = [x for x in rows if x['role_bucket_as_filed'] == D and 'airbnb' in x['who_performs'].lower()]
print('filed Done naming Airbnb in who column', len(named), [x['task_no'] for x in named])
print('Done survivors', [x['task_no'] for x in rows if x['role_bucket_corrected'] == D])
print('role fails', [x['task_no'] for x in rows if x['role_verdict'] == F])
print('auto fails', [x['task_no'] for x in rows if x['automation_verdict'] == F], 'auto none', [x['task_no'] for x in rows if x['automation_verdict'] == N])
print('auto filed', collections.Counter(x['automation_rating'] for x in rows), 'corrected', collections.Counter(x['automation_corrected'] for x in rows))
print('auto src types', collections.Counter(x['automation_source_type'] for x in rows if x['automation_verdict'] == S))
print('role src types', collections.Counter(x['role_source_type'] for x in rows if x['role_verdict'] == S))
print('No role survivors', sum(x['role_verdict'] == S and x['role_bucket_as_filed'] == X for x in rows))
