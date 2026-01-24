# TransXChange to GTFS Converter

This directory contains a pinned version of the Node.js `transxchange2gtfs` tool.

## Setup

Install dependencies (only needed once, or after version updates):

```bash
cd tools/transxchange2gtfs
npm install
```

## Usage

### Via npm script:
```bash
npm run convert -- input.zip output-gtfs.zip
```

### Via npx (from project root):
```bash
npx --prefix tools/transxchange2gtfs transxchange2gtfs input.zip output-gtfs.zip
```

### With environment variables:
```bash
NODE_OPTIONS=--max-old-space-size=8192 \
AGENCY_TIMEZONE=Europe/London \
AGENCY_LANG=en \
npm run convert -- input.zip output-gtfs.zip
```

## Options

- `--update-stops`: Force refresh NaPTAN stop data
- `--skip-stops`: Skip downloading stop data (if already cached)

## Documentation

See upstream project: https://github.com/planarnetwork/transxchange2gtfs

## License

The `transxchange2gtfs` package is licensed under GNU GPLv3.
