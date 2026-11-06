# Booked nights

Booked nights = homes × open nights × conversion. The filings give the total, and this folder splits it into guests, trips and stay length.

Back to the [walk through the equation](../README.md).

## Nights split into guests, trips and stay length

![Nights split into guests, trips and stay length](nights_split/nights_split.png)

- **Sample.** Airbnb filings for nights, dated reviewer accounts for guests.
- **Interval.** Guests 17% to 26%, trips -1.9% to +5.3%, stay length -2.9% to -4.2%.
- **Cannot establish.** Who the new accounts are. A new id can be a returning person.
- **Test against it.** The product of the terms rebuilds +18.9%, and the guest term is modelled from reviews on surviving listings.
- **Files.** [nights_split.py](nights_split/nights_split.py), [account_identity.csv](nights_split/account_identity.csv), [terms.csv](nights_split/terms.csv)
