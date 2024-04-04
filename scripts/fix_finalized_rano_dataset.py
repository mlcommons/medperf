import re
import os
import tarfile
from medperf import config
from medperf.init import initialize
from typer import Option, Typer, run

app = Typer()

REVIEWED_PATTERN = r".*?\/([^\/]*)\/(((?!finalized|under_review).)*)\/(((?!finalized|under_review).)*_tumorMask_model_0\.nii\.gz)"


def main(
        dataset_uid: str = Option(None, "-d", "--dataset"),
        tarball_path: str = Option(..., "-t", "--tarball")
):
    initialize()
    dset_path = os.path.join(config.datasets_folder, dataset_uid)
    labels_path = os.path.join(dset_path, "labels")

    with tarfile.open(tarball_path, 'r') as tar:
        for member in tar.getmembers():
            review_match = re.match(REVIEWED_PATTERN, member.name)
            if review_match is None:
                continue

            id, tp, *_ = review_match.groups()
            dest_path = os.path.join(
                labels_path,
                id,
                tp
            )
            dest_filename = f"{id}_{tp}_final_seg.nii.gz"
            # 1. Find the label related to this review
            member.name = dest_filename
            target_file = os.path.join(dest_path, dest_filename)

            if os.path.exists(target_file):
                os.remove(target_file)

            tar.extract(member, dest_path)


if __name__ == "__main__":
    run(main)