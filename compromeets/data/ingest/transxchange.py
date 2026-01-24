"""TransXChange to GTFS conversion using the transxchange2gtfs Node.js tool."""

import os
import subprocess
import sys
from pathlib import Path


class TransXChangeConverter:
    """Wrapper for the transxchange2gtfs Node.js CLI tool."""

    def __init__(
        self,
        agency_timezone: str = "Europe/London",
        agency_lang: str = "en",
        agency_url: str | None = None,
        max_memory_mb: int = 8192,
    ):
        """
        Initialize the converter with default settings.

        Args:
            agency_timezone: GTFS agency timezone (default: Europe/London)
            agency_lang: GTFS agency language code (default: en)
            agency_url: Optional default agency URL
            max_memory_mb: Node.js max memory in MB (default: 8192)

        """
        self.agency_timezone = agency_timezone
        self.agency_lang = agency_lang
        self.agency_url = agency_url
        self.max_memory_mb = max_memory_mb

    def convert(
        self,
        input_path: Path | str,
        output_path: Path | str,
        update_stops: bool = False,
        skip_stops: bool = False,
    ) -> None:
        """
        Convert TransXChange data to GTFS format.

        Args:
            input_path: Path to TransXChange file(s) - can be:
                - Single .xml file
                - .zip file containing multiple .xml files
                - Directory containing .xml files
                - Multiple paths can be passed as a list
            output_path: Path where GTFS .zip file will be written
            update_stops: Force refresh of NaPTAN stop data
            skip_stops: Skip downloading NaPTAN stop data (use cached)

        Raises:
            subprocess.CalledProcessError: If conversion fails
            FileNotFoundError: If Node.js or transxchange2gtfs is not installed

        """
        input_path = Path(input_path)
        output_path = Path(output_path)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build environment
        env = os.environ.copy()
        env["NODE_OPTIONS"] = f"--max-old-space-size={self.max_memory_mb}"
        env["AGENCY_TIMEZONE"] = self.agency_timezone
        env["AGENCY_LANG"] = self.agency_lang
        if self.agency_url:
            env["AGENCY_URL"] = self.agency_url

        # Build command
        # Use npx with --prefix to run from the tools directory
        project_root = Path(__file__).parent.parent.parent.parent
        tools_dir = project_root / "tools" / "transxchange2gtfs"

        cmd = [
            "npx",
            "--prefix",
            str(tools_dir),
            "transxchange2gtfs",
        ]

        if update_stops:
            cmd.append("--update-stops")
        if skip_stops:
            cmd.append("--skip-stops")

        cmd.extend([str(input_path), str(output_path)])

        # Run conversion
        try:
            result = subprocess.run(cmd, check=False, env=env, capture_output=True, text=True)

            # Print stdout/stderr for visibility
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)

            # Check if output file was actually created
            if not output_path.exists():
                error_msg = f"TransXChange conversion failed - output file not created.\nExit code: {result.returncode}"
                if result.stderr:
                    error_msg += f"\nError: {result.stderr}"
                raise RuntimeError(error_msg)

            # Check exit code
            if result.returncode != 0:
                print(f"Warning: transxchange2gtfs returned exit code {result.returncode} but output file exists")

        except FileNotFoundError as e:
            msg = (
                "Node.js or transxchange2gtfs not found. "
                "Install Node.js and run: cd tools/transxchange2gtfs && npm install"
            )
            raise FileNotFoundError(msg) from e


def convert_transxchange_to_gtfs(
    input_path: Path | str,
    output_path: Path | str,
    update_stops: bool = False,
    skip_stops: bool = False,
) -> None:
    """
    Convenience function to convert TransXChange to GTFS with default settings.

    Args:
        input_path: Path to TransXChange file(s) or directory
        output_path: Path where GTFS .zip file will be written
        update_stops: Force refresh of NaPTAN stop data
        skip_stops: Skip downloading NaPTAN stop data (use cached)

    """
    converter = TransXChangeConverter()
    converter.convert(input_path, output_path, update_stops=update_stops, skip_stops=skip_stops)
