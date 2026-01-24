"""Script for converting TransXChange data to GTFS format.

This script uses the transxchange2gtfs Node.js tool to convert TransXChange
timetable data (from BODS or other sources) into GTFS format.

Example usage:
    python scripts/ingest_transxchange.py \\
        compromeets/artifacts/bods_transxchange/operator.zip \\
        compromeets/artifacts/bods_gtfs.zip
"""

import tempfile
import shutil
import sys
import os
from pathlib import Path
import zipfile
import pandas as pd
from compromeets.data.ingest.transxchange import convert_transxchange_to_gtfs

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


def fix_stop_coordinates(gtfs_path: Path, naptan_csv: Path) -> None:
    """Fix stop coordinates using NAPTAN data.
    
    The transxchange2gtfs package doesn't handle Easting/Northing coordinates
    from TfL's TransXChange files, so we need to update them from NAPTAN data.
    """
    print("\nFixing stop coordinates from NAPTAN data...")
    
    # Build NAPTAN coordinate lookup (ATCOCode -> (lat, lon))
    print("  Loading NAPTAN data...")
    naptan_coords = {}
    with open(naptan_csv, 'r', encoding='utf-8') as f:
        reader = pd.read_csv(f, usecols=['ATCOCode', 'Latitude', 'Longitude'])
        for _, row in reader.iterrows():
            atco = row['ATCOCode']
            lat = row['Latitude']
            lon = row['Longitude']
            # Only store if coordinates are valid (non-zero)
            if pd.notna(lat) and pd.notna(lon) and lat != 0 and lon != 0:
                naptan_coords[atco] = (float(lat), float(lon))
    
    print(f"  Loaded {len(naptan_coords)} NAPTAN stops with coordinates")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Extract GTFS
        with zipfile.ZipFile(gtfs_path, 'r') as z:
            z.extractall(temp_path)
        
        # Fix stops.txt coordinates
        stops = pd.read_csv(temp_path / 'stops.txt')
        original_zeros = len(stops[(stops['stop_lat'] == 0) & (stops['stop_lon'] == 0)])
        
        updated = 0
        missing = []
        
        for idx, row in stops.iterrows():
            stop_id = row['stop_id']
            
            # If coordinates are already valid, skip
            if row['stop_lat'] != 0 or row['stop_lon'] != 0:
                continue
                
            # Look up in NAPTAN
            if stop_id in naptan_coords:
                lat, lon = naptan_coords[stop_id]
                stops.at[idx, 'stop_lat'] = lat
                stops.at[idx, 'stop_lon'] = lon
                updated += 1
            else:
                missing.append(stop_id)
        
        # Save updated stops
        stops.to_csv(temp_path / 'stops.txt', index=False)
        
        # Recreate zip
        with zipfile.ZipFile(gtfs_path, 'w', zipfile.ZIP_DEFLATED) as z:
            for file in temp_path.iterdir():
                if file.is_file():
                    z.write(file, file.name)
        
        print(f"  ✓ Updated {updated} stops with NAPTAN coordinates")
        if missing:
            print(f"  ⚠ Warning: {len(missing)} stops not found in NAPTAN data")
            if len(missing) <= 10:
                print(f"    Missing stops: {', '.join(missing[:10])}")


def fix_gtfs_issues(gtfs_path: Path) -> None:
    """Fix common issues in transxchange2gtfs output."""
    
    print("\nFixing GTFS issues...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Extract
        with zipfile.ZipFile(gtfs_path, 'r') as z:
            z.extractall(temp_path)
        
        # Fix routes.txt - replace 'undefined' route_type
        routes = pd.read_csv(temp_path / 'routes.txt')
        undefined_count = len(routes[routes['route_type'] == 'undefined'])
        if undefined_count > 0:
            routes.loc[routes['route_type'] == 'undefined', 'route_type'] = '0'
            routes['route_type'] = pd.to_numeric(routes['route_type'], errors='coerce')
            routes.to_csv(temp_path / 'routes.txt', index=False)
            print(f"  ✓ Fixed {undefined_count} routes with undefined route_type")
        
        # Fix calendar_dates.txt - remove duplicates
        calendar_dates = pd.read_csv(temp_path / 'calendar_dates.txt')
        original_count = len(calendar_dates)
        calendar_dates = calendar_dates.drop_duplicates(subset=['service_id', 'date'], keep='last')
        removed = original_count - len(calendar_dates)
        if removed > 0:
            calendar_dates.to_csv(temp_path / 'calendar_dates.txt', index=False)
            print(f"  ✓ Removed {removed} duplicate calendar_dates entries")
        
        # Recreate zip
        with zipfile.ZipFile(gtfs_path, 'w', zipfile.ZIP_DEFLATED) as z:
            for file in temp_path.iterdir():
                if file.is_file():
                    z.write(file, file.name)

def main():
    """Convert TransXChange to GTFS."""
    if len(sys.argv) < 3:
        print("Usage: python scripts/ingest_transxchange.py <input_path> <output_path>")
        print("\nExample:")
        print("  python scripts/ingest_transxchange.py \\")
        print("    compromeets/artifacts/journey-planner-timetables.zip \\")
        print("    compromeets/artifacts/tfl-gtfs.zip")
        sys.exit(1)

    create_naptan_zip()

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        sys.exit(1)

    print(f"Converting TransXChange to GTFS...")
    print(f"  Input:  {input_path}")
    print(f"  Output: {output_path.absolute()}")
    print()

    try:
        convert_transxchange_to_gtfs(
            input_path=input_path,
            output_path=output_path,
            # Note: The package will output zeros for lat/lon since it can't handle
            # Easting/Northing from TfL's TransXChange files. We fix this afterward.
            update_stops=False,
            skip_stops=True,  # Use cached NAPTAN data, don't try to download
        )

        # Fix coordinates using NAPTAN data
        naptan_csv = Path("compromeets/artifacts/Stops.csv")
        if naptan_csv.exists():
            fix_stop_coordinates(output_path, naptan_csv)
        else:
            print(f"\n⚠ Warning: NAPTAN Stops.csv not found at {naptan_csv}")
            print("  Stop coordinates will not be updated")

        # Fix other GTFS issues
        fix_gtfs_issues(output_path)

        print()
        print(f"✓ Conversion complete: {output_path.absolute()}")
        
        # Show file size if created
        if output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"  File size: {size_mb:.1f} MB")
    except Exception as e:
        print(f"\n✗ Conversion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
