# Limits on every inventory figure, 6 Nov 2026

Intervals are 95%. "Count" means a full read of a file, so no sampling interval applies. "Census" means the Inside Airbnb files, which are complete for their regions and carry selection of their own. Structured rival samples have unknown inclusion probabilities, so they carry no interval.

## Stock
| Figure | Sample | Interval | What a reader needs |
|---|---|---|---|
| 6,934,269 sitemap pages, Nov 2026 | All 139 files | Count | The sitemap lists pages Airbnb gives search engines, so it omits about 34% of the viewable estimate. |
| 10,447,450 ids, Apr 2026 | All 213 files | Count | The index held 213 files for one month, and Airbnb has not explained the change. |
| 10.47m viewable listings | 1,710,831 census listings, 499 fetched ids | 10.34m to 10.60m | The interval covers sampling alone, and the census under-represents listings that never sell, so the true figure more likely sits above it. |
| 11.3m viewable, upper read | April file reach of 92.1% of census listings | None | The figure assumes the missing 7.9% of census listings is typical. |
| 88.1% of out-of-sitemap ids live | 440 of 499 ids | 85.0% to 90.7% | The ids come from the census, so never-sold listings outside it are unseen. |
| 19.4% of viewable listings with no review, about 2.0m | 1,489 sitemap pages, 440 outside pages | 17.5% to 21.1% | Reviews undercount stays, so a page with no review may still have sold. |
| 8.45m listings with a review | Same two samples | 8.26m to 8.64m | The interval holds the 10.47m fixed, so it understates total uncertainty. |
| 2.34m ids in the April file alone | Ten-snapshot panel | Count | Ids missing from other snapshots may be rotation, so this is an upper read on never-sold pages. |
| Guest Favorite 37.5% inside, 7.0% outside | 559 of 1,489, 7.0% of 440 | 35.1% to 40.0%, 5.0% to 9.8% | The badge read comes from one November 2026 page fetch. |
| About 2.8m Guest Favorite listings | Same two samples | 2.66m to 3.05m | The interval holds the 10.47m fixed, and Airbnb's "top 2 million" was said in May 2024. |

## Sitemap filter and growth
| Figure | Sample | Interval | What a reader needs |
|---|---|---|---|
| Inclusion 87% at month 11, 57% at month 13 | 1,710,831 census listings | Census | The 12-month rule is inferred from the data, and Airbnb has not published it. |
| Steady inclusion 75% to 92% | 272,903 listings active throughout | Census | Levels before August 2025 are not comparable, because the list partly rotated. |
| Ten-city inclusion 77.0% to 83.7% | Reviewed listings in ten cities | Census | Ten large cities stand in for the whole sitemap. |
| Sitemap growth 21% raw, near 11% adjusted | Jan to Nov 2026 sitemaps | None | The adjustment applies a ten-city change to a global count, so 11% is an estimate with no interval. |

## Survival
| Figure | Sample | Interval | What a reader needs |
|---|---|---|---|
| 16.15m ids in the union, 9.22m absent | Ten snapshots, 61.7m rows read | Count | Ids that never reached a sitemap are unseen, and files before August 2025 cover 75% to 99% of the index. |
| 86.75% of absent ids withdrawn | 347 of 400 ids | 83.1% to 89.7% | A 410 covers deletion and unlisting, and a host can relist, so it means no longer viewable. |
| About 8.0m ids no longer viewable | 400 ids applied to 9.22m | 7.66m to 8.27m | One sample of 400 sets the whole count, and the wording stays "no longer viewable". |
| 24% yearly loss, 2023 ids | 82 ids, age 3.35 years | 21% to 27% | The interval covers the live share alone and takes the 3.35-year age as given. |
| 29% yearly loss, 2024 ids | 68 ids, age 2.35 years | 25% to 31% | The same limit applies, and these rates cover ids that reached a sitemap. |

Survival cells from the 400 sampled ids. Each cell applies its live share to the ids absent in November 2026, and ids still in the sitemap are counted in full.

| Cell | Live of fetched | Viewable share | Interval | Status |
|---|---|---|---|---|
| Ids dated before 2023 | 32 of 204 | 44.6% | 41.7% to 48.3% | Usable |
| Ids dated 2023 | 10 of 82 | 39.0% | 35.2% to 45.1% | Usable with interval |
| Ids dated 2024 | 7 of 68 | 45.3% | 42.1% to 51.1% | Usable with interval |
| Ids dated 2025 and 2026 | 4 of 46 | 75.1% | 73.7% to 78.3% | Thin, 4 live ids |
| First seen Mar 2023 | 26 of 170 | 42.3% | 39.1% to 46.5% | Background |
| First seen Nov 2023 | 7 of 57 | 39.8% | 35.5% to 47.3% | Background |
| First seen May 2024 | 4 of 40 | 39.3% | 35.2% to 48.1% | Thin |
| First seen Nov 2024 | 4 of 44 | 41.8% | 38.3% to 49.6% | Thin |
| First seen Feb 2025 | 5 of 33 | 48.0% | 42.8% to 57.7% | Thin |
| First seen Jun 2025 | 4 of 19 | 56.2% | 49.2% to 68.5% | Do not quote |
| First seen Aug 2025 | 3 of 18 | 61.8% | 56.8% to 72.1% | Do not quote |
| First seen Jan 2026 | 0 of 16 | 65.6% | 65.6% to 72.3% | Do not quote |
| First seen May 2026 | 0 of 3 | 78.0% | 78.0% to 90.4% | Do not quote |

A cell with 4 live ids rests on those 4 pages, and its interval looks narrow because ids still in the sitemap are counted in full. Collection hit 2 rate-limit responses and 30 seconds of a second worker, and duplicates were dropped.

## Flows, ten cities
| Figure | Sample | Interval | What a reader needs |
|---|---|---|---|
| 24.3% exit in nine months, near 31% a year | 95,202 of 392,070 listings, Dec 2025 to Sep 2026 | Census | Ten large cities over nine months stand in for a global rate, and leaving the file can mean unlisting. |
| 19.1% joined | 74,992 listings | Census | New ids made 78.9% of arrivals, and the rest were older ids returning. |
| 65.0% of leavers' hosts gone from the city | 95,202 leavers | Census | Gone means no listing left in that city, and the host may still list elsewhere. |
| 17.9% replaced like for like | 95,202 leavers | Census | The match uses same host, room type and bedrooms, so it can miss a replacement under a new host. |
| 45.9% of leavers reviewed in the prior 12 months | 95,202 leavers | Census | Reviews undercount stays, so the active share of leavers is a lower read. |

## Mix and concentration
| Figure | Sample | Interval | What a reader needs |
|---|---|---|---|
| North America 21.1% of listings | 308 of 1,463 located pages | 19.0% to 23.2% | The share is of sitemap pages, so it reflects the 12-month filter. |
| 109 nights a listing, North America | 308 pages against reported nights | 99 to 120 | The denominator is sitemap pages, so nights per viewable listing run lower. |
| 44.8% of 2024+ listings from new hosts | Random sitemap pages | 41.4% to 48.3% | New host means joined within nine months before the listing, read from the page. |
| 35.9% of 2026 ids from new hosts, so 64% established | 94 of 262 pages | 30.3% to 41.9% | Recent ids are few and still filling, so the share can move. |
| 49.1% of 2025 new homes from first-time owners | 46,733 homes in `new_owners/new_home_owner.csv` | None | The script behind this file was not kept, so its panel and its first-owner test cannot be re-derived, and it needs rebuilding before print. |
| Top 10% hold 50.3% of reviews, top 1% hold 10.4% | 1,710,831 census listings | Census | Reviews stand in for stays, and the census favours large cities. |
| Hosts with 2 to 9 listings hold 34.0% of listings, 39.4% of reviews | Census, within-region shares | Census | Host size is counted inside each region file, so a global operator splits across regions. |
| Companies hold 22.5% of Catalonia's flats, 58.6% of Barcelona's | 104,502 and 10,651 register units | Count | Two registers in one region say nothing on company share elsewhere. |
| Registration text on 96.2%, 83.6%, 33.3%, 19.4% of pages (Italy, Spain, France, United States) | 78, 67, 165, 279 pages | 89.3% to 98.7%, 72.9% to 90.6%, 26.6% to 40.8%, 15.1% to 24.4% | Text on a page shows a field was filled, and it does not show a valid licence. |

## Rival overlap
Rates are shares of keyed rival rows found on Airbnb. None has an interval, and the range shows how far census and rival weights move the rate.

| Figure | Sample | Reweighted range | What a reader needs |
|---|---|---|---|
| Seattle Booking 97.3% | 543 of 558 keyed, 773 of 801 rows (96.5%) | 97.3% to 97.6% | Another 215 rows have no key, so 70.2% is the floor across all rows. |
| Seattle Vrbo 91.2% | 364 of 399 keyed, 35.8% of reported homes | 90.2% to 91.3% | Vrbo's total counts homes open for one December week. |
| San Diego Booking 95.2% | 298 of 313 keyed, 23.1% of reported rows | 95.1% to 95.2% | One city search sorted by review score reads well-reviewed homes first. |
| San Diego Vrbo 83.2% | 247 of 297 keyed, 10.4% of reported homes | 83.0% to 83.9% | The pull stopped at 345 rows, under the 385 target. |
| Lisbon Vrbo 74.7% | 236 of 316 keyed, 9.9% of reported homes | 74.7% to 76.4% | This is a floor, because Airbnb key coverage in Lisbon is 68%. |
| Hawaii Vrbo 60.9% | 238 of 391 keyed, 4.5% on 19 of 38 boxes | 60.5% to 61.8% | This is a floor, and island rates run from 32.0% to 75.8%. |
| Hawaii Booking 69.4%, directional | 218 of 314 keyed, 3.8% of reported rows | 67.7% to 74.1% | Quote about 70%, because census weights put it below the 69.4% and windward Oahu was never searched. |
| Lisbon Booking 73.8%, directional | 175 of 237 keyed, 4.9% of reported rows | 68.0% to 73.8% | The rate describes central Lisbon, since 70 rows came from Brazil and Croatia and searches reach 38.3% of the total. |
| Seattle 12.5% of homes on Booking | 568 of 4,538 homes | Bounds 10.5% to 18.2% | The bounds come from identification, and `overlap/claim.md` holds the reasoning. |
| Seattle 80.5% on neither rival, directional | 3,653 of 4,538 homes | About 68.0% to 80.5% | Vrbo is a partial pull, so 80.5% is a ceiling and 68.0% assumes unseen rows repeat no match. |

**The 200 hand checks were never done.** The study plan set 200 hand-checked pairs as the gate for reportable precision and false-miss rates, and the study closed without them, because listing photos could not be reviewed in bulk and the US Airbnb files lack titles. No human-measured false-match rate exists for any rival overlap figure. Key matches rest on exact licence numbers, and bedrooms agree on 82.7% of joined Seattle Booking rows. The hidden-key ladder test covers San Diego and Seattle only and measures the coordinate rungs, which is why they stay uncounted.

## Other sources
| Figure | Sample | Interval | What a reader needs |
|---|---|---|---|
| Spain 341,001 homes, down 10.7% | INE, May 2026 against May 2025 | Published count | The fall follows a removal order, so it reads as enforcement and says little on demand. |
| Vrbo 2,091,797 URLs against Airbnb's 5.45m | Archived December 2022 files | Count | The count is nearly four years old, and no later public Vrbo file exists. |
| Booking.com 3,574,140 property URLs | Public sitemap, 230 countries | Count | The file holds hotels and homes together, and listing pages returned a challenge. |
| Agoda 5,749,403 property slugs | Public sitemap | Count | Duplicates and stale pages were never tested. |
| Airbnb lead over Booking.com, 5.8 times to 0.8 times | Sampled pages scaled by country | Wide, in the workbook | Germany's 0.8 times rests on 39 pages, and cells under 30 pages are indicative. |
| No Google hotel within 700 m, Seattle 46.9%, Lisbon 3.3% | 4,549 and 17,075 homes | None | Places shows November 2026 only, and OpenStreetMap gives 67.6% and 16.2%, so quote the order and a range. |
