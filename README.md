A Python app for finding where to meet, between multiple people.

# Usage

`notebooks/isochrone_testing.ipynb` has the full flow. Download the required map files from the list below, then make sure the names line up with the paths in the notebook. Run `uv sync` to set up your environment, and then point your ipynb kernel to the newly created `.venv` folder.

To load environment variables from your local `.env` file into `uv`, add the following to your `.zshrc`:

```sh
# load .env if it exists in the current directory
_set_uv_env_file() {
    if [-f .env]; then
        export UV_ENV_FILE=.env
    else
        unset UV_ENV_FILE
    fi
}

# reset when changing directories
autoload -U add-zsh-hook
add-zsh-hook chpwd _set_uv_env_file

# set initially
_set_uv_env_file
```

You will need **GOOGLE_PLACES_API_KEY** to be set

# Open source maps

- [Protomaps](https://protomaps.com/) (Regional)
- [Geofabrik](https://download.geofabrik.de/europe/united-kingdom/england/greater-london.html) (City-level)
- [BODS (Bus Data)](https://data.bus-data.dft.gov.uk/timetable/download/)
- [ONS Postcodes](https://geoportal.statistics.gov.uk/search?tags=onspd)

# Appendix: trans2gtfs updates

Things to update in `transx2gtfs` if needed (at the moment all the necessary open source transit data is already in GTFS):

- deprecate `append()`
- update URL for stops from `naptan.app` to new one
- Handle missing enddate change

```python
# replace
section_ref = jp.JourneyPatternSectionRefs.cdata
# with:
if isinstance(jp.JourneyPatternSectionRefs, list): # If it's a list, take the first one
section_ref = jp.JourneyPatternSectionRefs[0].cdata
else:
section_ref = jp.JourneyPatternSectionRefs.cdata

# Likewise

# Route Section reference (might be needed somewhere) - can be a single element or a list

if isinstance(r.RouteSectionRef, list): # If it's a list, take the first one
    route_section_id = r.RouteSectionRef[0].cdata
else: # Single element
    route_section_id = r.RouteSectionRef.cdata

# and

# Service description - may not exist

if hasattr(service, 'Description') and hasattr(service.Description, 'cdata'):
    service_description = service.Description.cdata
else:
    service_description = "" # Empty string if Description is missing

mode = get_mode(service.Mode.cdata if hasattr(service, 'Mode') else 'bus')

# get_route_tye:

mode = data.TransXChange.Services.Service.Mode.cdata if hasattr(data.TransXChange.Services.Service, 'Mode') else 'bus'
```
