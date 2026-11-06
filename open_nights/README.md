# Open nights

Open nights are the days a home offers for sale. Host size and a second site move them.

Back to the [walk through the equation](../README.md).

## The 12.5% as a sum over host size and open days

![The 12.5% as a sum over host size and open days](calendar/calendar_split.png)

- **Sample.** 4,538 Seattle homes. Open days are unbooked nights over the next 365 days in the September 2026 file.
- **Interval.** 4.6% to 6.6%, 8.1% to 11.1%, 16.2% to 22.7% and 33.3% to 41.1% for the four groups.
- **Cannot establish.** That calendars cause sharing. A home sold on two sites can hold more open days for that reason alone.
- **Test against it.** The four groups sum exactly to 12.5%, and the largest, most open group supplies 4.8 points. Floors by group sit in the results file.
- **Files.** [calendar_split.py](calendar/calendar_split.py), [seattle_home_cells.csv](../homes/overlap/seattle_home_cells.csv)

## Shared homes add open nights under the same host

![Shared homes add open nights under the same host](same_host/same_host.png)

- **Sample.** 65 Seattle hosts with 871 homes and 119 San Diego hosts with 1,982 homes that hold both shared and unshared homes.
- **Interval.** Seattle open nights 8.1 to 46.9, San Diego 10.8 to 29.8. Airbnb nights -9.6 to 14.2 and -11.9 to 2.6.
- **Cannot establish.** Displacement. Airbnb nights are estimates built from reviews, and the sample is hosts who chose to share some homes.
- **Test against it.** A host fixed-effect comparison with bedrooms and capacity, clustered by host. Airbnb nights move +2.3 (p=0.71) and -4.6 (p=0.21).
- **Data note.** `host_moments.csv` holds per-host sums of squares and cross-products, with hosts anonymised. These are enough for the slope and clustered errors with no home rows.
- **Files.** [same_host.py](same_host/same_host.py), [host_moments.csv](same_host/host_moments.csv)
