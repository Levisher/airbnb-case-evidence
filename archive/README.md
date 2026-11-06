# Source builds

These scripts document how the committed tables were made. They read files kept outside this repo, so they cannot run here, and `reproduce.py` does not call them. The term folders run from committed tables.

- `export_conversion.py`, `export_homes.py` and `export_rest.py` converted source files into the committed tables.
- `audit/` holds the scripts that first produced each audit result.
- `price_map/`, `rival_overlap/` and `operating_leverage/` hold the upstream analysis called by those scripts.
- `weekly_sitemap.py` collects the Friday data behind `homes/weekly`.

Local paths were shortened, and the card panel vendor's name was removed. Keys were read from a local file, and none is included here. Collection scripts for rival pulls are excluded.
