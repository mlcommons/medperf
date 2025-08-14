import typer
from pathlib import Path
import tempfile
import os
import subprocess

from encrypt_utils import generate_fernet_key_and_encrypt

app = typer.Typer()


@app.command('generate_key_and_encrypt_container')
def generate_key_and_encrypt(
    key_output_path: Path = typer.Option(
        ...,
        '-k',
        '--key-output-path',
        dir_okay=False,
        writable=True,
        help='Output path for generate Fernet key'),
    docker_image_name: str = typer.Option(
        None,
        '-d',
        '--docker-image',
        help='Name (including tag) of Docker image to encrypt. '
             'Must be present locally, will not be pulled.'),
    singularity_image_file: Path = typer.Option(
        None,
        '-s',
        '-a',
        '--singularity-image',
        '--apptainer-image',
        dir_okay=False,
        readable=True,
        exists=True,
        help='Singularity/Apptainer image to encrypt.'),
    encrypted_image_output_path: Path = typer.Option(
        ...,
        '-e',
        '--encrypted-image-output-path',
        dir_okay=False,
        writable=True,
        help='Output path for encrypted container image'),
):
    """
    Generates a Fernet key and encrypts a Docker or Singularity image.
    Exactly one of 'docker_image_name' or 'singularity_image_file' MUST be provided!
    """
    if (docker_image_name is None and singularity_image_file is None) or \
       (docker_image_name is not None and singularity_image_file is not None):
        raise ValueError("Exactly one of 'docker_image_name' or "
                         "'singularity_image_file' MUST be provided!")

    with tempfile.TemporaryDirectory() as tmp_dir:

        if singularity_image_file:
            file_to_encrypt = singularity_image_file
        else:

            docker_archive_file = os.path.join(tmp_dir, 'archive.tar')

            subprocess.run(['docker', 'save', docker_image_name, '-o', docker_archive_file])
            file_to_encrypt = docker_archive_file

        key = generate_fernet_key_and_encrypt(file_to_encrypt=file_to_encrypt,
                                              encrypted_image_output_path=encrypted_image_output_path)
        with open(key_output_path, 'wb') as key_file:
            key_file.write(key)


if __name__ == '__main__':
    app()
