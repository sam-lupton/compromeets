import multiprocessing
import os
import tempfile
import warnings
import zipfile
from pathlib import Path

import pandas as pd
import transx2gtfs
from transx2gtfs import agency, stops

# Set to True for single-threaded debugging
SINGLE_THREADED = True

# Runs, but doesn't save all data successfully


def get_agency_url(operator_code):
    """Get url for operators. Must return a valid URL (scheme://...) for GTFS/r5py."""
    operator_urls = {
        "OId_LUL": "https://tfl.gov.uk/maps/track/tube",
        "OId_DLR": "https://tfl.gov.uk/modes/dlr/",
        "OId_TRS": "https://www.thamesriverservices.co.uk/",
        "OId_CCR": "https://www.citycruises.com/",
        "OId_CV": "https://www.thamesclippers.com/",
        "OId_WFF": "https://tfl.gov.uk/modes/river/woolwich-ferry",
        "OId_TCL": "https://tfl.gov.uk/modes/trams/",
        "OId_EAL": "https://www.emiratesairline.co.uk/",
    }
    if operator_code in list(operator_urls.keys()):
        return operator_urls[operator_code]
    # GTFS requires a valid URL; r5py rejects "NA" or other non-URLs.
    return "https://www.gov.uk/bus-open-data"


def get_agency(data):
    """Parse agency information from TransXchange elements - patched to use concat instead of append"""
    # Container
    agency_data = pd.DataFrame()

    # Agency id
    agency_id = data.TransXChange.Operators.Operator.get_attribute("id")

    # Agency name
    agency_name = data.TransXChange.Operators.Operator.OperatorNameOnLicence.cdata

    # Agency url
    agency_url = get_agency_url(agency_id)

    # Agency timezone
    agency_tz = "Europe/London"

    # Agency language
    agency_lang = "en"

    # Parse row
    agency = {
        "agency_id": agency_id,
        "agency_name": agency_name,
        "agency_url": agency_url,
        "agency_timezone": agency_tz,
        "agency_lang": agency_lang,
    }

    # Use concat instead of deprecated append
    agency_data = pd.concat([agency_data, pd.DataFrame([agency])], ignore_index=True, sort=False)
    return agency_data


# Patch the agency module - use direct module reference to avoid pylance error
agency.get_agency = get_agency  # type: ignore[assignment]


def _patched_txc_21_style_stops(data):
    # Attributes
    _stop_id_col = "stop_id"

    # Container
    stop_data = pd.DataFrame()

    # Get stop database
    naptan_stops = stops.read_naptan_stops()

    # Iterate over stop points using TransXchange version 2.1
    for p in data.TransXChange.StopPoints.AnnotatedStopPointRef:
        # Stop_id
        stop_id = p.StopPointRef.cdata

        # Get stop info
        stop = naptan_stops.loc[naptan_stops[_stop_id_col] == stop_id]

        if len(stop) == 0:
            # Try first to refresh the Stop data
            stops._update_naptan_data()
            naptan_stops = stops.read_naptan_stops()
            stop = naptan_stops.loc[naptan_stops[_stop_id_col] == stop_id]

            # If it could still not be found warn and skip
            if len(stop) == 0:
                warnings.warn(f"Did not find a NaPTAN stop for '{stop_id}'", UserWarning, stacklevel=2)
                continue

        elif len(stop) > 1:
            raise ValueError("Had more than 1 stop with identical stop reference.")

        # Add to container
        stop_data = pd.concat([stop_data, stop], ignore_index=True, sort=False)

    return stop_data


stops._get_txc_21_style_stops = _patched_txc_21_style_stops


# Create ZIP file from your downloaded Stops.csv - only if it doesn't exist
def create_naptan_zip():
    """Create NaPTAN_data.zip from the downloaded Stops.csv file"""
    temp_dir = tempfile.gettempdir()
    target_dir = os.path.join(temp_dir, "transx2gtfs")
    target_zip = os.path.join(target_dir, "NaPTAN_data.zip")

    # Only create if it doesn't exist
    if os.path.exists(target_zip):
        return target_zip

    # Create directory if it doesn't exist
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Path to your downloaded CSV
    stops_csv = Path("compromeets/artifacts/Stops.csv")

    if not stops_csv.exists():
        raise FileNotFoundError(f"Stops.csv not found at {stops_csv}")

    # Create ZIP file with Stops.csv inside
    with zipfile.ZipFile(target_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(stops_csv, arcname="Stops.csv")

    print(f"Created NaPTAN ZIP at: {target_zip}")
    return target_zip


# Create the ZIP file before conversion (only once in main process)
create_naptan_zip()

# Patch multiprocessing.Pool for single-threaded debugging
if SINGLE_THREADED:
    original_pool = multiprocessing.Pool

    def single_threaded_pool(*args, **kwargs):
        # Force processes=1 for debugging
        kwargs["processes"] = 1
        return original_pool(*args, **kwargs)

    multiprocessing.Pool = single_threaded_pool  # type: ignore[assignment]
    print("Running in single-threaded mode for debugging")

if __name__ == "__main__":
    data_dir_for_transxchange_files = (
        "compromeets/artifacts/bods_transxchange/bodds_archive_20260120_JP7n6KU/Abellio London Ltd_27"
    )
    output_path = "compromeets/artifacts/bods_gtfs.zip"
    # Pass worker_cnt=1 for single-threaded mode
    worker_count = 1 if SINGLE_THREADED else None
    transx2gtfs.convert(data_dir_for_transxchange_files, output_path, worker_cnt=worker_count)
