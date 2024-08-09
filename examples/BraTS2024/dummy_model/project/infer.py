import os
import shutil

from numpy.random import randint
import pandas as pd


def run_inference(data_path, parameters, output_path):
    task = parameters["task"]
    if task == "segmentation-radiotherapy":
        for k in os.listdir(data_path):
            file = os.path.join(data_path, k, f"{k}_t1c.nii.gz")
            shutil.copyfile(file, os.path.join(output_path, f"{k}.nii.gz"))
    else:
        dummy_predictions = pd.DataFrame({'SubjectID': os.listdir(data_path)})
        dummy_predictions["Prediction"] = randint(6,size=len(os.listdir(data_path)))
        dummy_predictions.to_csv(os.path.join(output_path, "predictions.csv"), index=False)
