import argparse
from utils.package import package
from utils.validate import is_valid


def get_args():
    desc = (
        "Helper script to prepare an MLCube for medperf/challenge submission.\n"
        + "This script will create a 'deploy' path with the files that need to be hosted\n"
        + "for medperf mlcube submission. Additionally, if an output path is provided,\n"
        + "all deployment files are packaged into the output tarball file. Useful for competitions"
    )

    parser = argparse.ArgumentParser(prog="PackageMLCube", description=desc)
    parser.add_argument(
        "mlcube",
        help="Path to the mlcube folder. This path is the one that contains ./mlcube.yaml and ./workspace",
    )
    parser.add_argument(
        "--output",
        help="(Optional) Output tarball path. If provided, the contents of the deploy folder are packaged into this file",
    )
    return parser.parse_args()


def main():
    args = get_args()
    mlcube_path = args.mlcube
    output_path = args.output

    if not is_valid(mlcube_path):
        exit()

    package(mlcube_path, output_path)


if __name__ == "__main__":
    main()
    print("✅ Done!")
