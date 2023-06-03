import os
import yaml
import argparse
import pandas as pd


def get_statistics(data_df: pd.DataFrame) -> dict:
    """Computes statistics about the data. This statistics are uploaded
    to the Medperf platform under the data owner's approval. Include
    every statistic you consider useful for determining the nature of the
    data, but keep in mind that we want to keep the data as private as
    possible.

    Args:
        data_df (pd.DataFrame): DataFrame containing the prepared dataset

    Returns:
        dict: dictionary with all the computed statistics
    """
    stats = {
        "weight": {
            "mean": float(data_df["weight"].mean()),
            "std": float(data_df["weight"].std()),
            "min": float(data_df["weight"].min()),
            "max": float(data_df["weight"].max()),
        },
        "volume": {
            "mean": float(data_df["volume"].mean()),
            "std": float(data_df["volume"].std()),
            "min": float(data_df["volume"].min()),
            "max": float(data_df["volume"].max()),
        },
        "density": {
            "mean": float(data_df["density"].mean()),
            "std": float(data_df["density"].std()),
            "min": float(data_df["density"].min()),
            "max": float(data_df["density"].max()),
        },
        "size": len(data_df),
    }

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser("MedPerf Statistics Example")
    parser.add_argument(
        "--data_path",
        dest="data",
        type=str,
        help="directory containing the prepared data",
    )
    parser.add_argument(
        "--labels_path",
        dest="labels",
    )
    parser.add_argument(
        "--out_file", dest="out_file", type=str, help="file to store statistics"
    )

    args = parser.parse_args()

    namesfile = os.path.join(args.data, "data.csv")
    names_df = pd.read_csv(namesfile)

    stats = get_statistics(names_df)

    with open(args.out_file, "w") as f:
        yaml.dump(stats, f)
