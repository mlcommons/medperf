from medperf.init import initialize
from container_hashes_utils import get_container_yamls
import typer
from pathlib import Path
initialize()

app = typer.Typer()

@app.command()
def main(
    include_public_links: bool = typer.Option(
        False,
        '-p',
        '--public-link',
        '--public_link',
        help="Include containers where the container-config file is a public link, such as a GitHub file."
        "At least one of 'include_public_links' and/or 'include_synapse' must be set to True."
    ),
    include_synapse: bool = typer.Option(
        False,
        '-s',
        '--synapse',
        help="Include containers where the container-config file is a Synapse link. "
        "Please run the 'medperf synapse login' command to authenticate with Synapse "
        "before running this command with this option."
        "At least one of 'include_public_links' and/or 'include_synapse' must be set to True."
    ),
    output_public_file: Path = typer.Option(
        Path('public.csv'),
        '--output-public-file',
        '--output_public_file',
        help="Output path for the CSV file with updated Container IDs for the containers with Public linke."
        "Defaults to 'public.csv' in the current directory if not set."
    ),
    output_synapse_file: Path = typer.Option(
        Path('synapse.csv'),
        '--output-synapse-file',
        '--output_synapse_file',
        help="Output path for the CSV file with updated Container IDs for the containers with Synapse links."
        "Defaults to 'synapse.csv' in the current directory if not set."
    ),
):  
    if not include_public_links and not include_synapse:
        raise ValueError("At least one of the '-p' and/or '-s' flags must be set!")
    
    get_container_yamls(include_public_links=include_public_links,
                        include_synapse_links=include_synapse,
                        output_public_path=output_public_file,
                        output_synapse_path=output_synapse_file)


if __name__ == '__main__':
    app()
