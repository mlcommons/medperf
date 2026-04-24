from container_hashes_utils import get_container_hashes
import typer
from pathlib import Path


app = typer.Typer()
DEFAULT_OUTPUT_NAME = "updated_containers.json"


@app.command()
def main(
    input_json: Path = typer.Option(
        ...,
        "-i",
        "--input",
        help="Input JSON file generated from the sibling script 'get_containr_info_from_medperf.py'.",
    ),
    output_json: Path = typer.Option(
        Path(DEFAULT_OUTPUT_NAME).resolve,
        "-o",
        "--output",
        help="Output path for the CSV file with updated Container IDs for the containers."
        f"Defaults to '{DEFAULT_OUTPUT_NAME}' in the current directory if not set.",
    ),
    exclude_synapse: bool = typer.Option(
        False,
        "-s",
        "--exclude-synapse",
        "--exclude_synapse",
        help="Set option to ignore Containers hosted in the Synapse platform.",
    ),
):
    get_container_hashes(
        input_json=input_json, exclude_synapse=exclude_synapse, output_json=output_json
    )


if __name__ == "__main__":
    app()
