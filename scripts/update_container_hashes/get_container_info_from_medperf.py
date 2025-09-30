from medperf.init import initialize
from container_hashes_utils import get_container_jsons
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
    output_file: Path = typer.Option(
        Path('containers.json'),
        '-o',
        '--output-file',
        '--output_file',
        help="Output json file with the container info from the MedPerf server."
        "Defaults to 'containers.json' in the current directory if not set.",
        writable=True,
        dir_okay=False,
        file_okay=True
    )
):
    if not include_public_links and not include_synapse:
        raise ValueError("At least one of the '-p' and/or '-s' flags must be set!")

    get_container_jsons(include_public_links=include_public_links,
                        include_synapse_links=include_synapse,
                        output_file=output_file)


if __name__ == '__main__':
    app()
