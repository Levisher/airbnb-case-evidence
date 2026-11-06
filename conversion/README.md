# Conversion

Conversion is the share of open nights that sell. Reviews, hotel prices and repeat guests affect it.

Back to the [walk through the equation](../README.md).

## The review coefficient falls from 0.346 to 0.029

![The review coefficient falls from 0.346 to 0.029](review_effect/review_effect.png)

- **Sample.** 89,546 homes across 768 city, neighbourhood and bedroom cells in ten cities. Errors are clustered across 271 neighbourhoods.
- **Interval.** Before, 0.335 to 0.356. After, 0.019 to 0.040. Split-sample instrument, -0.110 to -0.092.
- **Cannot establish.** That review depth causes bookings. Reviews proxy past demand, and 2025 reviews sit on the path being tested, so 0.029 is a low reading and the true figure remains unproven.
- **Test against it.** **The failed test.** Absorbing 2025 reviews cuts the coefficient from 0.346 to 0.029, prior reviews' added R-squared from 0.152 to 0.0008, and the Booking.com gap from 2.1x to 1.07x. The instrument gives -0.101. By depth, the absorbed coefficient is -0.043, 0.007, 0.081 and 0.139, placing any effect on deep homes. On blocked nights, 55% survives in a fit explaining 18.7% of variation.
- **Data note.** `moments_*.csv` hold X'X and X'y by neighbourhood. They reproduce the coefficients, clustered errors, R-squared and Shapley shares without publishing home rows.
- **Files.** [review_effect.py](review_effect/review_effect.py), [moments_all_homes.csv](review_effect/moments_all_homes.csv), [moments_band_26_to_100.csv](review_effect/moments_band_26_to_100.csv), [moments_band_3_to_5.csv](review_effect/moments_band_3_to_5.csv), [moments_band_6_to_25.csv](review_effect/moments_band_6_to_25.csv), [moments_band_over_100.csv](review_effect/moments_band_over_100.csv), [moments_calendar.csv](review_effect/moments_calendar.csv)

## Airbnb holds 90.3% of reviews on matched homes

![Airbnb holds 90.3% of reviews on matched homes](review_depth/review_depth.png)

- **Sample.** 693 homes matched to Booking.com in three markets, 810 including Lisbon, and 748 matched to Vrbo.
- **Interval.** None.
- **Cannot establish.** A conversion advantage. Review stocks also reflect time on site and review habits.
- **Test against it.** Adding Lisbon reduces 90.3% to 80.9%. The note's 65.8% uses four markets, while the same three markets give 74.6%. Vrbo reads 38.8% on that test. Its ahead share reruns at 69.9% against 68.9% printed.
- **Files.** [review_depth.py](review_depth/review_depth.py), [matched_home_sums.csv](review_depth/matched_home_sums.csv), [same_home_coldstart.csv](review_depth/same_home_coldstart.csv)

## Review content holds where review counts fail

![Review content holds where review counts fail](review_content/review_content.png)

- **Sample.** 89,546 homes for booked share, 133,164 listings for exit by rating, 137,653 for exit by depth and 54,820 for the price premium.
- **Interval.** None. These are census cuts.
- **Cannot establish.** That scores cause outcomes. Better homes can score higher and remain listed longer for their own reasons.
- **Test against it.** Exit uses snapshot pairs, where 13% to 15% of reviews vanished across three cities. Months to 25 reviews uses 57,720 surviving homes, excluding slow homes that left.
- **Files.** [review_content.py](review_content/review_content.py), [conv_by_trust.csv](review_content/conv_by_trust.csv), [exit_by_depth.csv](review_content/exit_by_depth.csv), [exit_by_rating.csv](review_content/exit_by_rating.csv), [rebuild_months.csv](review_content/rebuild_months.csv), [same_host_depth.csv](review_content/same_host_depth.csv)

## Return by stay number is mostly selection

![Return by stay number is mostly selection](stay_ladder/stay_ladder.png)

- **Sample.** 7.47m reviewed stays from 2019 to 2024 across ten cities.
- **Interval.** Plus or minus 0.03 points at stay 1 and 0.47 at stay 5.
- **Cannot establish.** That each stay makes the next more likely. Frequent travellers stay more, and the remaining effect cannot be separated from review habits.
- **Test against it.** A selection-only model reproduces 87.1% of the rise on cells rerun here. The free fit retains 46.9% on stays and 73.3% on trips. Same-guest gaps fall 25.8% pooled and 15.6% for guests first seen from 2022. An 18.5% rise in review habit produces the same fall. Lost reviews between snapshots reduce the ladder by up to about 6%.
- **Data note.** `selection_cells.csv` holds stay number by tenure cells. Other files contain aggregate tables. Reviewer ids are excluded.
- **Files.** [stay_ladder.py](stay_ladder/stay_ladder.py), [repeat_paths.csv](stay_ladder/repeat_paths.csv), [same_guest_gaps.csv](stay_ladder/same_guest_gaps.csv), [selection_cells.csv](stay_ladder/selection_cells.csv), [stay_ladder_refit.csv](stay_ladder/stay_ladder_refit.csv), [stay_ladder_tests.csv](stay_ladder/stay_ladder_tests.csv)

## Return ratios within one card panel

![Return ratios within one card panel](card_panel/card_panel.png)

- **Sample.** Licensed card panel covering new-customer groups from July 2025 to July 2026.
- **Interval.** None. Annual attrition of 1.75% moves the 13.3% reading by about 1.3% of its value.
- **Cannot establish.** Any customer or spending level. These are panel ratios, and Airbnb discloses no series for comparison.
- **Test against it.** Each reading is tested for bias direction and attrition. Booking.com is not comparable because pay-at-property guests never enter the panel. The note prints panel spend as dollars, so this folder retains ratios only.
- **Data note.** Ratios only. Customer counts, spend levels and panel rows are excluded.
- **Files.** [card_panel.py](card_panel/card_panel.py), [card_older_group.csv](card_panel/card_older_group.csv), [card_ratios.csv](card_panel/card_ratios.csv), [matched_group_shares.csv](card_panel/matched_group_shares.csv), [spend_ratio_vrbo.csv](card_panel/spend_ratio_vrbo.csv)

## Lisbon homes against hotel rooms

![Lisbon homes against hotel rooms](hotel_price/hotel_price.png)

- **Sample.** 273 Lisbon homes with offers for 12 to 15 March 2027, compared with hotels within 1 km.
- **Interval.** None.
- **Cannot establish.** A market-wide price advantage. The test covers one city and one set of dates, using offers read in November 2026.
- **Test against it.** Against the cheapest quarter of nearby hotels, homes read 1.08x, with 39% cheaper. The 0.66x assumes two guests per hotel room and an unchanged home price for six.
- **Data note.** Ratios are grouped by bedroom count. Offer prices are excluded. The note's larger-home and price-per-guest figures have no output table, and the ledger marks them.
- **Files.** [hotel_price.py](hotel_price/hotel_price.py), [lisbon_cheapest_quarter.csv](hotel_price/lisbon_cheapest_quarter.csv), [lisbon_ratio_all.csv](hotel_price/lisbon_ratio_all.csv), [lisbon_ratio_by_bedrooms.csv](hotel_price/lisbon_ratio_by_bedrooms.csv)

## The Google layer

![The Google layer](location/location.png)

- **Sample.** 777 cells of 1 km and 4,662 Places Aggregate counts, from 4,844 requests and 196 console errors. The 1 km Routes layer has 1,554 elements. The Routes account used 8,890 of 10,000 free elements, including a lost run and a 500 m rerun.
- **Interval.** Gain intervals are in `gmp_cells.csv`.
- **Cannot establish.** Anything before November 2026. Places data is current and cannot date hotels or homes back to 2022.
- **Test against it.** R-squared gains are measured over property fields, neighbourhood and held-out data. The gain over neighbourhood is 0.3 to 0.6 points outside Maui. The held-out gain is -0.2 to 0.0 outside Maui. Hotel shares preserve market rankings, and OpenStreetMap gives higher levels.
- **Data note.** Market summaries only. Google cell counts stay out under Google's terms, so the script cannot rerun regressions. It rebuilds call totals and reads the gains.
- **Files.** [location.py](location/location.py), [gmp_cells.csv](location/gmp_cells.csv)
