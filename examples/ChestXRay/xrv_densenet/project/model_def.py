import os
import pandas as pd
import torch
import torchxrayvision as xrv
from torch.utils.data import DataLoader
import typer
import yaml
from tqdm import tqdm

from data.dataset import XRVDataset
import models

xrv.models = models

app = typer.Typer()


class XRVInference(object):
    @staticmethod
    def run(data_path, params_file, weights, out_path):
        with open(params_file, "r") as f:
            params = yaml.full_load(f)

        densenet = xrv.models.DenseNet
        available_models = set(
            ["all", "rsna", "nih", "pc", "chex", "mimic_nb", "mimic_ch"]
        )

        if params["model"] in available_models:
            model = densenet(weights=params["model"], weights_filename_local=weights)
        else:
            print("The specified model couldn't be found")
            exit()

        preds = []
        data = XRVDataset(data_path)
        with torch.no_grad():
            for sample in tqdm(data):
                out = model(torch.from_numpy(sample["img"]).unsqueeze(0))
                preds.append([sample["Path"]] + out.tolist()[0])

        pred_cols = ["Path"] + model.pathologies
        preds_df = pd.DataFrame(data=preds, columns=pred_cols)
        preds_df.to_csv(out_path, index=False)


@app.command("infer")
def infer(
    data_path: str = typer.Option(..., "--data_path"),
    params_file: str = typer.Option(..., "--params_file"),
    weights: str = typer.Option(..., "--weights"),
    out_path: str = typer.Option(..., "--out_path"),
):
    XRVInference.run(data_path, params_file, weights, out_path)


if __name__ == "__main__":
    app()
