# Contribution per night

Contribution per night is GBV per night times take rate less variable cost, or $16.73 in FY2025. The fee, the price and who carries property cost move it.

Back to the [walk through the equation](../README.md).

## What a point of take rate is worth

![What a point of take rate is worth](take_rate/take_rate.png)

- **Sample.** FY2025, year to Q2 2026 and year to Q3 2026 filings.
- **Interval.** 9.2% to 11.4% across periods and marketing treatments.
- **Cannot establish.** What a fee rise would cost. This is a break-even, and no file shows a listing's fee plan, so no test measures the demand response.
- **Test against it.** Take rate fell from 13.57% to 13.19% and stands at 13.32%, so the fee claim has yet to show in results. FY2024 sits above the 13% to 13.5% range the note gives for the last two years.
- **Data note.** `filing_lines.csv`, `take_rate_grid.csv`. The 0.03% and 0.70% price responses in the note have no output table.
- **Files.** [take_rate.py](take_rate/take_rate.py), [take_rate_grid.csv](take_rate/take_rate_grid.csv), [filing_lines.csv](../filing_lines.csv)

## Bookings a rival must replace

![Bookings a rival must replace](replacement/replacement.png)

- **Sample.** A 4.1-night stay with a $948 host take. KeyData Q2 2026 channel shares for US managed homes.
- **Interval.** 90.2% for Vrbo at its earlier 8% fee. Review proxy by market runs 24.9 to 126.4 for Vrbo and 7.7 to 72.6 for Booking.com.
- **Cannot establish.** Recapture. Delivered figures are income hosts already earn, so neither measure tests what a rival would win if a host left.
- **Test against it.** A second delivered measure with no review counts. On revenue direct reads 67.4, and it reached 100.0 in Q2 2025, before the single fee. Single-home hosts have no measure without review counts.
- **Files.** [replacement.py](replacement/replacement.py), [channel_shares.csv](replacement/channel_shares.csv), [replacement_test.csv](replacement/replacement_test.csv)

## Airbnb, Vacasa and Sonder per $100

![Airbnb, Vacasa and Sonder per $100](per_100/per_100.png)

- **Sample.** Three 10-Ks for FY2024: Airbnb, Vacasa as manager, Sonder as lessee.
- **Interval.** $22.06 to $24.07 for Sonder on estimated bookings, by tax rate.
- **Cannot establish.** That the rental model loses. Sonder's gap splits 33.6% marketing, 34.8% overhead, 20.9% rescue cost and 10.4% VAT and bad debt, so one failed company proves about a third of the case.
- **Test against it.** The line after direct cost and support is level at 0.3% of the gap, in FY2024 alone. It read -$0.62 for Sonder in FY2023.
- **Files.** [per_100.py](per_100/per_100.py), [gap_split.csv](per_100/gap_split.csv), [per100_lines.csv](per_100/per100_lines.csv)
