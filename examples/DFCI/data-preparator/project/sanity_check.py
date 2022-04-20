import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from PIL import Image



def clip_dicom(image_array):
    image_array[image_array>240] = 240.
    image_array[image_array<-160] = -160.
    image_array = (image_array - np.min(image_array)) / (np.max(image_array) - np.min(image_array) + 1e-12)
    return image_array

def sanity_check(file):
    """Runs a few checks to ensure data quality and integrity
    Args:
        names_df (pd.DataFrame): DataFrame containing transformed data.
    """
    # Here you must add all the checks you consider important regarding the
    # state of the data
    # assert names_df.columns.tolist() == ["First Name", "Last Name"], "Column mismatch"
    # assert names_df["First Name"].isna().sum() == 0, "There are empty fields"
    # assert names_df["Last Name"].isna().sum() == 0, "There are empty fields"
    files_df = os.listdir(file)
    synapse_i = os.path.join(file,files_df[0])
    synapse_i = np.load(synapse_i)

    
    # def check_label(i, l):
    print("Checking Label Dimensions:")
    print(synapse_i.shape)
    # print(l.shape)
    print("Checking image view")
    for index in range(synapse_i.shape[0]):
        if np.sum(synapse_i[index, :, :]*255) > 0:
            print(index)
            fig, ax = plt.subplots(figsize=(10, 10))
            # plt.imshow(i[index, :, :]*255, cmap='gray')
            plt.imshow(synapse_i[index, :, :], cmap='jet', alpha=0.5)
            plt.show()
            
            

            
if __name__ == '__main__':
    parser = argparse.ArgumentParser("Medperf Model Sanity Check Example")
    parser.add_argument("--data_path", dest="data", type=str, help="directory containing the prepared data")

    args = parser.parse_args()

    #file = os.path.join(args.data, "synapse_train/")
    file = args.data
    print(file)
    files_df = os.listdir(file)
    print(files_df)
    sanity_check(os.path.join(file))