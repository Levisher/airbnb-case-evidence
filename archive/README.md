# Source builds

These scripts are the record of how the committed tables were made. They read files that stay out of this repo, so they cannot run here, and `reproduce.py` does not call them. Everything in the term folders runs from committed tables.

- `export_conversion.py`, `export_homes.py` and `export_rest.py` turned the source files into the committed tables.
- `audit/` holds the scripts that first produced each audit result.
- `price_map/`, `rival_overlap/` and `operating_leverage/` hold the upstream analysis those scripts call.

Local paths were shortened and the card panel vendor's name was removed. Keys were always read from a local file, and none is here. Collection scripts for the rival pulls are left out.
