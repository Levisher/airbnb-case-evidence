# Seattle overlap claim, 6 Nov 2026

## Printed claim
In Seattle, 568 of 4,538 licensed Airbnb whole homes (12.5%) carried a licence number that also appeared on Booking.com, within bounds of 10.5% to 17.9%, so 82.1% to 89.5% were not found on Booking.com.

Basis: Inside Airbnb file of September 2026, entire homes under 30 nights with a licence, against Booking.com rows pulled on 5 November 2026. The word "exclusive" stays out of print, because only Booking.com is tested at census depth.

| Bound | Airbnb homes on Booking.com | Share found | Share not found |
|---|---|---|---|
| Floor | 476 | 10.5% | 89.5% |
| Home-level match | 568 | 12.5% | 87.5% |
| Ceiling | 811 | 17.9% | 82.1% |
| Widest bound, with 15 rows whose key Airbnb lacks | 826 | 18.2% | 81.8% |

## Reasoning for each bound
**Floor, 476 homes.** One licence can cover several Airbnb listings, so a key on Airbnb is credited only up to the number of Booking.com rows carrying it. A Booking.com row proves one unit, and this count takes no more than that. The floor assumes each key match is correct, and that was never hand-checked.

**Home-level match, 568 homes.** Any Airbnb home whose licence number appears on a Booking.com row counts. The 543 joined rows carry 420 distinct keys, which reach 568 homes, or 1.05 homes per joined row. This count credits every listing under a shared licence, so it can overstate when a building licence covers units sold on Airbnb alone.

**Ceiling, 811 homes.** Every Booking.com row with no key evidence either way is counted as one more Airbnb home.
- 215 rows carry no licence, and all 215 show Booking.com's "not required" flag.
- 28 rows sit between the 773 used and the 801 reported: 8 unread, 10 hotel types and 10 outside the market.

That adds 243 to 568. The bound counts rows and uses no coordinate pick, so it stays inside the ladder test.

**Widest bound, 826 homes.** A further 15 keyed rows have a licence absent from the Airbnb file, which is keyed evidence against a match. Counting them anyway gives 18.2%, the figure in the footnote of the note. At 1.05 homes per row it would reach 18.5%.

## Why keyed matches alone are counted
Only licence-key matches count, because with keys hidden the coordinate rung found the right home for 51.2% of 508 known Seattle Booking.com pairs and still picked a home for 89.4% of rows whose true twin had been removed, so a nearby home is no evidence of a match.

- Coordinates picked a home for 153 of the 215 unkeyed rows (71.2%), below the 89.4% false-pick rate, so they show no twin among those rows.
- The strictest rung, unique pick with bedrooms, implies a true share of unkeyed rows from -30.9% to 56.9% depending on radius, so the unkeyed rows stay unresolved.

## Host size split
| Host listings | Homes | Found on Booking.com | 95% interval | Floor | Share of Airbnb nights |
|---|---|---|---|---|---|
| 1 | 2,220 | 5.2% | 4.3% to 6.2% | 4.8% | 48.7% |
| 2 to 5 | 1,166 | 10.8% | 9.2% to 12.7% | 6.9% | 25.9% |
| 6 to 20 | 544 | 22.4% | 19.1% to 26.1% | 17.9% | 11.5% |
| 21 or more | 608 | 33.7% | 30.1% to 37.6% | 31.3% | 13.9% |

## Calendar split
Open days are unbooked nights over the next 365 days in the September 2026 file.

| Group | Share of homes | Found on Booking.com | 95% interval | Floor | Points of the 12.5% |
|---|---|---|---|---|---|
| 1 to 5 homes, open up to 240 days | 44.2% | 5.5% | 4.6% to 6.6% | 3.9% | 2.4 |
| 1 to 5 homes, open over 240 days | 30.4% | 9.5% | 8.1% to 11.1% | 8.0% | 2.9 |
| 6 or more homes, open up to 240 days | 12.4% | 19.2% | 16.2% to 22.7% | 17.1% | 2.4 |
| 6 or more homes, open over 240 days | 13.0% | 37.1% | 33.3% to 41.1% | 32.4% | 4.8 |

Among homes open up to 240 days, host size moves the rate from 5.5% to 19.2%. Among hosts with 1 to 5 homes, the calendar moves it from 5.5% to 9.5%. The last group holds 13.0% of homes and 219 of the 568 matches. Intervals describe the group rates only, and the floor and ceiling above are the wider limits on the headline.

The calendar link has no proven direction, because a home sold on two sites can hold more open days for that reason alone. Under the same host, shared homes had 27.5 more open nights (p=0.006) and 2.3 more Airbnb nights (SE 6.1, p=0.71), on 65 hosts and 872 homes. Shared there means found on Booking.com or Vrbo, and Airbnb nights are estimates built from reviews.

## Both rivals together
Not found on Booking.com or Vrbo is 80.5% of homes and 82.6% of estimated nights, and both are ceilings because the Vrbo pull reached 35.8% of the homes it reported. Scaling the 317 Vrbo-only homes by that share gives about 68.0% of homes and 73.1% of nights. The both-rivals figure is directional, and the wording that fits is "roughly 68% to 80%". San Diego's 90.6% stays out of print, since the same scaling gives 58.1%.

## Readings the number must never carry
- Exclusive to Airbnb. Only Booking.com is tested at census depth, and own sites, Vrbo's unread rows and other channels sit outside it.
- A market-wide or national rate. It covers licensed homes in Seattle, and 121 unlicensed eligible homes sit outside the 4,538.
- A rate for any other city. Seattle is the one market with a near-census of Booking.com.
- Amateur hosts stay on Airbnb alone. Single-listing hosts show 5.2%, and that is a lower overlap, with no statement on their other channels.
- Booking dependence. Presence on a site says nothing about where the nights came from.
- Airbnb captures the booking or controls the guest. Overlap measures listings and says nothing on guests.
- Pricing power or take-rate headroom. Prices were not part of this match.
- Rival supply is a subset of Airbnb. That is the reverse test, 543 of 558 keyed rows, and 215 rows have no key.
- A trend. This is one file against one pull, with a two-month gap, and no earlier date can be built from it.
- A host's decision. A home absent from Booking.com may have been refused, never tried or removed, and the data cannot tell these apart.
