import re
import os
import tarfile
from typer import Option, Typer, run

app = Typer()

REVIEWED_PATTERN = r".*?\/([^\/]*)\/(((?!finalized|under_review).)*)\/(((?!finalized|under_review).)*_tumorMask_model_0\.nii\.gz)"
EXTRACT_PATH = ".tmp_reviewed"


def main(
        tarball_path: str = Option(..., "-t", "--tarball")
):

    with tarfile.open(tarball_path, 'r:gz') as tar:
        tar.extractall(path=EXTRACT_PATH)

    


if __name__ == "__main__":
    run(main)