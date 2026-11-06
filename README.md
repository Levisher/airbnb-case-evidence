# Airbnb case study

This repo holds the data work behind a two-page case study on Airbnb's growth and profitability. Each figure links to its data, script, sample, interval and test. Supply and disclosed financial metrics are checked weekly.

**EBITDA = booked nights × contribution per night − marketing − fixed cost**

**Booked nights = homes × open nights × conversion**

FY2025: $4,297m = 533m × [($171.24 × 13.41%) − $6.23] − $1,595m − $3,026m

## The three claims

| Claim | Status | Evidence |
|---|---|---|
| 1. Hosts fund homes and stay at Airbnb's fee | Weakened | Seattle overlap holds within a 10.5% to 17.9% band. Tasks done outright fell from 21 to 8. Take rate moved from 13.57% to 13.19%. |
| 2. Repeat guests and unpaid demand fill nights without rising marketing | Weakened | The review coefficient fell from 0.346 to 0.029. Selection explains 73% to 87% of the return ladder. The return lead over Expedia, Vrbo and Hilton holds. |
| 3. Added nights reach EBITDA on a light cost base | Holding | Nights supplied 74% of EBITDA growth from 2022 to 2025. Booking kept $11.51 of clean income per added night against Airbnb's $5.18. |

## Results that moved against me

| Test | Before | After | Folder |
|---|---:|---:|---|
| Review coefficient after absorbing 2025 reviews, 89,546 homes | 0.346 | 0.029 (0.019 to 0.040) | [conversion](conversion/) |
| Conversion gap to Booking.com | 2.1x | 1.07x (1.04x to 1.09x) | [conversion](conversion/) |
| Tasks Airbnb does outright after checking 54 role ratings | 21 | 8, with 16 ratings failed | [homes](homes/) |
| Seattle homes also on Booking.com, licence keys only | 12.5% | 10.5% to 17.9% | [homes](homes/) |

Coordinate matching found 33.4% to 67.4% of known pairs with keys hidden. It also selected a home for 85.8% to 99.7% of rows with no twin. Only licence-key matches count. The 200 planned hand checks were never completed.

## The walk through the equation

| Term | Reading | Limitation | Folder |
|---|---|---|---|
| EBITDA | $4,297m, up $1,394m from 2022 to 2025 | Excludes stock pay. FY2022 is a recovery base. | [ebitda](ebitda/) |
| Booked nights | 533m. Guests +22.0%, trips +1.1%, nights per trip -3.6% from 2023 to 2025 | Guests are modelled from reviewer accounts. Range 17% to 26%. | [booked_nights](booked_nights/) |
| Homes | 16,150,130 ids across ten snapshots. About 10.47m viewable. | 24.3% of listings left ten cities in nine months. Destination unknown. | [homes](homes/) |
| Open nights | Overlap ranges from 5.5% for small hosts to 37.1% for large hosts with open calendars | A home sold on two sites can hold more open days for that reason alone. | [open_nights](open_nights/) |
| Conversion | Strongest review records booked 51.8% of open nights. Weakest booked 34.0%. | Review depth failed. Selection reproduces 87.1% of the return ladder. | [conversion](conversion/) |
| Contribution per night | $16.73. One point of take rate is worth $1.71 per night. | The break-even has no measured demand response. | [contribution_per_night](contribution_per_night/) |
| Marketing | $1,595m. $1.75 per $100 of bookings against $4.40 at Booking. | Marketing per added night rose from $4.06 to $9.89 in H1 2026. | [marketing](marketing/) |
| Fixed cost | $3,026m, growing 15.0% annually | Booking kept $11.51 of clean income per added night against Airbnb's $5.18. | [fixed_cost](fixed_cost/) |

A 1% move in take rate or GBV per night moves FY2025 EBITDA by 2.85%. Homes, open nights and conversion each move it by 2.08%. Each cost line moves it by less than 0.8%. The sensitivity ranking is in [ebitda](ebitda/).

## Weekly tracking

| Series | Update | Failure trigger | Files |
|---|---|---|---|
| Airbnb sitemap listing ids, additions, removals and churn | Every Friday | Count moves 5% from November 2026, churn exceeds 10%, or last run is over 10 days old | [homes/weekly](homes/weekly/) |
| Net take, take rate, marketing per night, nights growth and EBITDA margin | Each 10-Q | A live line crosses its trigger | [ebitda/watch](ebitda/watch/) |

A local job reads the sitemaps with one worker and pushes the counts here. Collection runs outside GitHub's servers. A GitHub Action reruns the checks every Friday afternoon. A failed run means the tracker stopped or a trigger was crossed.

## Every figure

`figures.csv` records each figure's sample, interval, test and status. Holding means the figure reran without a failed test. Weakened means it holds within a stated limit. Dropped means it failed its test or lacks enough evidence to quote. Figures are checked against version 15 of the note, dated 6 November 2026.

<!-- table start -->
| Term | Holding | Weakened | Dropped |
|---|---|---|---|
| [ebitda](ebitda/) | 25 | 0 | 0 |
| [booked_nights](booked_nights/) | 5 | 0 | 0 |
| [homes](homes/) | 19 | 24 | 7 |
| [open_nights](open_nights/) | 9 | 0 | 0 |
| [conversion](conversion/) | 24 | 27 | 4 |
| [contribution_per_night](contribution_per_night/) | 13 | 4 | 0 |
| [marketing](marketing/) | 14 | 1 | 0 |
| [fixed_cost](fixed_cost/) | 17 | 0 | 0 |
| **All** | **126** | **56** | **11** |
<!-- table end -->

## Running it

Requirements are Python 3.12 and `pip install -r requirements.txt`.

```
python reproduce.py
```

The script runs each study from committed tables, compares results with `figures.csv` and checks that every file serves a figure. No scraping, API key or licensed file is required. The location script rebuilds call totals and reads market regression summaries because Google cell counts stay out of the repo.

## Kept out of this repo

| Source | Published here | Kept out |
|---|---|---|
| Inside Airbnb census | Aggregates and moment tables | Listing rows, ids, hosts, reviewers, coordinates |
| Sitemap and Wayback frame | Presence patterns and counts | The 16,150,130 ids |
| Booking.com and Vrbo pulls | Counts by market and match cells | Rival rows, licence numbers |
| Card panel | Ratios within the panel | Customer counts, spend levels, panel rows |
| Compustat | Ratios | Line items |
| Google Places and Routes | Market ratios and regression results | Cell counts |
| 10-K and 10-Q filings | Line items in `filing_lines.csv` | Nothing |

## Layout

```
ebitda/                   the equation, term ranking, peer frame, watch lines
booked_nights/            guests, trips and nights per trip
homes/                    frame, survival, overlap, task map, weekly supply
open_nights/              calendars and same-host tests
conversion/               reviews, location, hotel prices, return ladder, card panel
contribution_per_night/   take rate, replacement, per $100 peers
marketing/                net take and search share
fixed_cost/               added nights
archive/                  source builds, not rerun here
transcripts/              working sessions behind the data
figures.csv               every figure with its status and test
filing_lines.csv          filed lines used across studies
reproduce.py              runs and checks everything
```
