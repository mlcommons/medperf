import os
import argparse
import pandas as pd

def sanity_check(names_df):
    """Runs a few checks to ensure data quality and integrity

    Args:
        names_df (pd.DataFrame): DataFrame containing transformed data.
    """
    # Here you must add all the checks you consider important regarding the
    # state of the data
    assert names_df.columns.tolist() == ["First Name", "Last Name"], "Column mismatch"
    assert names_df["First Name"].isna().sum() == 0, "There are empty fields"
    assert names_df["Last Name"].isna().sum() == 0, "There are empty fields"

if __name__ == '__main__':
    parser = argparse.ArgumentParser("Medperf Model Sanity Check Example")
    parser.add_argument("--data_path", dest="data", type=str, help="directory containing the prepared data")

    args = parser.parse_args()

    names_file = os.path.join(args.data, "names.csv")
    names_df = pd.read_csv(names_file)

    sanity_check(names_df)