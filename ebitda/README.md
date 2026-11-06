# EBITDA

EBITDA = booked nights × contribution per night − marketing − fixed cost. This folder holds the equation, the ranking of its terms and the peer frame.

Back to the [walk through the equation](../README.md).

## The equation, rebuilt from filed lines

![The equation, rebuilt from filed lines](equation/equation.png)

- **Sample.** Airbnb 10-K lines, FY2022 to FY2025.
- **Interval.** None. This is an identity.
- **Cannot establish.** That the terms are independent. Fixed cost is the balance that closes the equation, and Adjusted EBITDA leaves out stock pay.
- **Test against it.** The identity closes to zero. The exact bridge terms are +$1,027m, +$870m, +$30m, -$201m and -$333m and sum to $1,394m. The note rounds per-night values first and prints +$866m, +$32m, -$197m and -$336m, which sum to $1,392m.
- **Files.** [equation.py](equation/equation.py), [filing_lines.csv](../filing_lines.csv)

## A 1% move in each term

![A 1% move in each term](ranking/ranking.png)

- **Sample.** FY2025 filed lines, and the year to Q3 2026 from the sensitivity grid.
- **Interval.** None. This is a derivative of the identity.
- **Cannot establish.** Which term will move. An elasticity says nothing on the likely change, and the nights figure holds marketing dollars fixed.
- **Test against it.** With 2% payment cost on GBV, GBV per night reads 2.42%. With marketing per night fixed, nights read 1.70%. For the year to Q3 2026 the order is the same at 2.75%, 2.03%, 0.72%, 0.64% and 0.38%.
- **Files.** [ranking.py](ranking/ranking.py), [sensitivity_grid.csv](ranking/sensitivity_grid.csv), [filing_lines.csv](../filing_lines.csv)

## Nine models on one frame

![Nine models on one frame](nine_models/nine_models.png)

- **Sample.** 153 company-years across 51 tickers from Compustat, with nine case companies.
- **Interval.** None.
- **Cannot establish.** The "most promising outlook" in the note, which is a judgement. Unlike models share no one volume unit, and 5 of the 9 tie volume to revenue as transacted value.
- **Test against it.** Year-on-year margin swings above 5 points, and whether volume rebuilds reported revenue.
- **Data note.** Ratios only. Compustat line items stay out, so counts here rebuild from `nine_frame_ratios.csv` and `nine_growth.csv`.
- **Files.** [nine_models.py](nine_models/nine_models.py), [nine_frame_ratios.csv](nine_models/nine_frame_ratios.csv), [nine_growth.csv](nine_models/nine_growth.csv)

## The five disclosed lines that would break the pick

![The five disclosed lines that would break the pick](watch/watch.png)

- **Sample.** Net take, TTM implied take rate, brand and performance marketing per night, Nights and Seats Booked growth and TTM Adjusted EBITDA margin, all from the 10-Q filed 5 November 2026.
- **Interval.** None. These are filed figures measured against triggers set on 6 November 2026.
- **Cannot establish.** Whether a trigger is the right level. The triggers are the author's own arithmetic on filed lines, and the nights trigger assumes GBV per night rises 6.2% again.
- **Test against it.** The script fails when a live line passes its trigger on the failure side, so a breach stops the weekly run. Net take holds 1.15% of headroom to its 11.33% floor and is the nearest of the four live lines. Take rate at 13.32% already sits under the 13.41% floor, and that test runs from the end of FY2026, so it reads grey until then.
- **Data note.** `watch_lines.csv` carries the reading, the trigger, the failure side, the date each test goes live and the filing it comes from. Update it when a 10-Q lands.
- **Files.** [watch.py](watch/watch.py), [watch_lines.csv](watch/watch_lines.csv)
