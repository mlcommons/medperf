import argparse
from utils.package import package
from utils.validate import validate_and_parse_manifest


def get_args():
    desc = (
        "Helper script to prepare an MLCube for medperf/challenge submission.\n"
        + "This script will create an 'assets' path with the files that need to be hosted\n"
        + "for medperf mlcube submission. Additionally, if an output path is provided,\n"
        + "all deployment files are packaged into the output tarball file. Useful for competitions"
    )

    parser = argparse.ArgumentParser(prog="PackageMLCube", description=desc)
    parser.add_argument(
        "--mlcube",
        help="Path to the mlcube folder. This path is the one that contains ./mlcube.yaml",
    )
    parser.add_argument(
        "--mlcube-types",
        help="""Comma-separated list of mlcube types to look for. Valid ones are:
        'prep' for a data preparation MLCube, 'prep-sep' for a data preparation MLCube with
        separate output labels path, 'model' for a model MLCube, and 'metrics' for a metrics MLCube.""",
    )
    parser.add_argument(
        "--output",
        help="(Optional) Output tarball path. If provided, the contents of the deploy folder are packaged into this file",
    )
    args = parser.parse_args()
    args.mlcube_types = args.mlcube_types.split(",")
    if not set(args.mlcube_types).issubset(["prep", "prep-sep", "model", "metrics"]):
        raise ValueError("Invalid MLCube type")
    return args


def main():
    args = get_args()
    mlcube_path = args.mlcube
    output_path = args.output
    mlcube_types = args.mlcube_types

    required_files = validate_and_parse_manifest(mlcube_path, mlcube_types)
    package(mlcube_path, required_files, output_path)


if __name__ == "__main__":
    main()
    print("✅ Done!")
