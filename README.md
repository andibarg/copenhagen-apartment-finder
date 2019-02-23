# copenhagen-apartment-finder
Scrape DBA and Boliga periodically for newly-listed apartments in Copenhagen, emailing you when one matches your search criteria.

## Disclaimer
This script is not to be used without permissions from DBA and Boliga. You should always comply with the terms and conditions of these websites.

## How to run
- Customize the `config.yaml` file with your search criteria
- `python setup.py install`
- `python apartment-finder.py`

If DBA/Boliga change their frontend, the parsing will need to be updated.
