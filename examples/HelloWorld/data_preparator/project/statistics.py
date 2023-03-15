import os
import yaml
import argparse
import pandas as pd

def get_statistics(names_df: pd.DataFrame) -> dict:
    """Computes statistics about the data. This statistics are uploaded
    to the Medperf platform under the data owner's approval. Include
    every statistic you consider useful for determining the nature of the
    data, but keep in mind that we want to keep the data as private as 
    possible.

    Args:
        names_df (pd.DataFrame): DataFrame containing the prepared dataset

    Returns:
        dict: dictionary with all the computed statistics
    """
    fname_len = names_df["First Name"].str.len()
    lname_len = names_df["Last Name"].str.len()

    stats = {
        "First Name": {
            "length mean": float(fname_len.mean()),
            "length std": float(fname_len.std()),
            "length min": int(fname_len.min()),
            "length max": int(fname_len.max())
        },
        "Last Name": {
            "length mean": float(lname_len.mean()),
            "length std": float(lname_len.std()),
            "length min": int(lname_len.min()),
            "length max": int(lname_len.max())
        },
        "size": len(names_df)
    }

    return stats

if __name__ == '__main__':
    parser = argparse.ArgumentParser("MedPerf Statistics Example")
    parser.add_argument("--data_path", dest="data", type=str, help="directory containing the prepared data")
    parser.add_argument("--out_file", dest="out_file", type=str, help="file to store statistics")

    args = parser.parse_args()

    namesfile = os.path.join(args.data, "names.csv")
    names_df = pd.read_csv(namesfile)

    stats = get_statistics(names_df)

    with open(args.out_file, "w") as f:
        yaml.dump(stats, f)

