import os
import yaml
import argparse
import pandas as pd
import numpy as np

def get_statistics(trainfile: str, testfile: str, labelfile: str):
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
    count1 = len(os.listdir(trainfile))
    count2 = len(os.listdir(testfile))
    count3 = len(os.listdir(labelfile))

    stats = {
        "Total Images": {
            "training images": float(count1),
            "testing images": float(count1),
        },
        "Number of Patients": {
            "length mean": float(count3)
    }}

    return stats

if __name__ == '__main__':
    parser = argparse.ArgumentParser("MedPerf Statistics Example")
    parser.add_argument("--data_path", dest="data", type=str, help="directory containing the prepared data")
    parser.add_argument("--out_file", dest="out_file", type=str, help="file to store statistics")
    parser.add_argument("--labels_path", dest="labels", type=str, help="path containing labels")

    args = parser.parse_args()

    #trainfile = os.path.join(args.data, "synapse_train")
    #testfile = os.path.join(args.data, "synapse_test")
    trainfile = args.data
    testfile = args.data
    labelfile = args.labels
    stats = get_statistics(trainfile, testfile, labelfile)

    with open(args.out_file, "w") as f:
        yaml.dump(stats, f)
