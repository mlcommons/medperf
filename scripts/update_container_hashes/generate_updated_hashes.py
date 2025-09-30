from container_hashes_utils import get_container_hashes
import typer
from pathlib import Path


app = typer.Typer()


@app.command()
def main(
    input_json: Path = typer.Option(
        ...,
        '-i',
        '--input',
        help="Input JSON file generated from the sibling script 'get_containr_info_from_medperf.py'."
    ),
    output_csv: Path = typer.Option(
        Path('new_hashes.csv'),
        '-o',
        '--output',
        help="Output path for the CSV file with updated Container IDs for the containers."
        "Defaults to 'new_hashes.csv' in the current directory if not set."
    ),
    exclude_synapse: bool = typer.Option(
        False,
        '-s',
        '--exclude-synapse',
        '--exclude_synapse',
        help='Set option to ignore Containers hosted in the Synapse platform.'
    )
):
    get_container_hashes(input_json=input_json, exclude_synapse=exclude_synapse,
                         output_csv=output_csv)


if __name__ == '__main__':
    app()
