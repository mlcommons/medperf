import os
import shutil
import argparse
import pandas as pd

def prepare(names: pd.DataFrame):
    """Takes a list of names and formats them into [First Name, Last Name]

    Args:
        names (pd.DataFrame): DataFrame containing the names to be prepared
    """
    names["First Name"] = names["Name"].str.split().str[0]
    names["Last Name"] = names["Name"].str.split().str[-2]
    names.drop("Name", axis="columns", inplace=True)

    return names

def get_names_df(files, column_name):
    names_files = os.listdir(args.names)
    csv_files = [file for file in names_files if file.endswith(".csv")]
    tsv_files = [file for file in names_files if file.endswith(".tsv")]
    txt_files = [file for file in names_files if file.endswith(".txt")]

    if len(csv_files):
        filepath = os.path.join(files, csv_files[0])
        df = pd.read_csv(filepath, usecols=[column_name])
        return df
    if len(tsv_files):
        filepath = os.path.join(files, tsv_files[0])
        df = pd.read_csv(filepath, usecols=[column_name], sep='\t')
        return df
    if len(txt_files):
        filepath = os.path.join(files, txt_files[0])
        with open(filepath, "r") as f:
            names = f.readlines()

        df = pd.DataFrame(data=names, columns=[column_name])
        return df

if __name__ == '__main__':
    parser = argparse.ArgumentParser("Medperf Data Preparator Example")
    parser.add_argument("--names_path", dest="names", type=str, help="path containing raw names")
    parser.add_argument("--labels_path", dest="labels", type=str, help="path containing labels")
    parser.add_argument("--out", dest="out" , type=str, help="path to store prepared data")

    args = parser.parse_args()

    # One of the intended use-cases of the data preparator cube
    # is to accept multiple data formats depending on the task needs
    names_df = get_names_df(args.names, "Name")
    prepared_names = prepare(names_df)

    # add the labels to the output folder. In this case we're going to assume
    # the labels will always follow the same format
    in_labels = os.path.join(args.labels, "labels.csv")
    out_labels = os.path.join(args.out, "labels.csv")
    shutil.copyfile(in_labels, out_labels)

    out_file = os.path.join(args.out, "names.csv")
    prepared_names.to_csv(out_file, index=False)