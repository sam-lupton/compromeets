# Quick Start Guide

## First Time Setup

```bash
# From project root
make setup-transxchange

# Or manually
cd tools/transxchange2gtfs
npm install
```

## Basic Usage from Python

```python
from pathlib import Path
from compromeets.data.ingest.transxchange import convert_transxchange_to_gtfs

# Convert a single TransXChange file or zip
convert_transxchange_to_gtfs(
    input_path=Path("data/transxchange.zip"),
    output_path=Path("data/output.gtfs.zip")
)
```

## Command Line Usage

```bash
# Using the Python wrapper script
uv run python scripts/ingest_transxchange.py input.zip output-gtfs.zip

# Direct Node.js usage (from project root)
npx --prefix tools/transxchange2gtfs transxchange2gtfs input.zip output-gtfs.zip
```

## Advanced Options

### Custom converter settings:
```python
from compromeets.data.ingest.transxchange import TransXChangeConverter

converter = TransXChangeConverter(
    agency_timezone="Europe/London",
    agency_lang="en",
    agency_url="https://example.com",
    max_memory_mb=8192  # For large datasets
)

converter.convert(
    input_path="input.zip",
    output_path="output.gtfs.zip",
    update_stops=True,  # Force refresh NaPTAN data
    skip_stops=False    # Or skip if already cached
)
```

### Processing multiple files:
```python
from pathlib import Path

# Process all operator zips in a directory
bods_dir = Path("compromeets/artifacts/bods_transxchange")
output_dir = Path("compromeets/artifacts/gtfs_feeds")
output_dir.mkdir(parents=True, exist_ok=True)

for operator_zip in bods_dir.glob("*.zip"):
    output_file = output_dir / f"{operator_zip.stem}_gtfs.zip"
    print(f"Converting {operator_zip.name}...")
    convert_transxchange_to_gtfs(operator_zip, output_file, skip_stops=True)
```

## Troubleshooting

### Memory Issues
If you get heap out of memory errors with large datasets:
```python
converter = TransXChangeConverter(max_memory_mb=16384)  # 16GB
converter.convert(input_path, output_path)
```

### NaPTAN Stop Data
- First run downloads ~200MB of stop data automatically
- Use `update_stops=True` to force refresh
- Use `skip_stops=True` to skip download (if already cached)
- Stop data is cached in system temp directory

### Node.js Not Found
Ensure Node.js is installed:
```bash
node --version  # Should show v14.x or higher
npm --version
```

Install via Homebrew (macOS):
```bash
brew install node
```

## File Format Support

The converter accepts:
- **Single .xml file**: TransXChange timetable file
- **.zip file**: Multiple TransXChange files
- **Directory**: Folder containing .xml files
- **Nested zips**: Automatically processed recursively

## Output

Creates a valid GTFS feed (.zip) containing:
- `agency.txt`
- `stops.txt` (from NaPTAN data)
- `routes.txt`
- `trips.txt`
- `stop_times.txt`
- `calendar.txt` / `calendar_dates.txt`
- `transfers.txt` (with interchange times)
