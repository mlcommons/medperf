"""Adapted from https://github.com/hongweilibran/BraSyn/blob/main/dropout_modality.py
"""

import os
import random
import numpy as np
import shutil


def drop_modalities(val_set_folder, val_set_missing, modality_list):
    if not os.path.exists(val_set_missing):
        os.makedirs(val_set_missing)

    # create a pseudo validation set by randomly dropping one modality
    np.random.seed(123456)  # fix random seed

    folder_list = os.listdir(val_set_folder)
    drop_index = np.random.randint(0, len(modality_list), size=len(folder_list))

    for count, ff in enumerate(folder_list):
        if not os.path.exists(os.path.join(val_set_missing, ff)):
            os.mkdir(os.path.join(val_set_missing, ff))

        file_list = os.listdir(os.path.join(val_set_folder, ff))
        print(modality_list[drop_index[count]] + " is droppd for case " + ff)

        for mm in file_list:
            if not modality_list[drop_index[count]] in mm:
                shutil.copyfile(
                    os.path.join(val_set_folder, ff, mm),
                    os.path.join(val_set_missing, ff, mm),
                )
