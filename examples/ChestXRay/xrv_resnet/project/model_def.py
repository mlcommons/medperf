import os
import pandas as pd
import torch
import torchxrayvision as xrv
from torchvision.transforms import Resize
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
    def run(data_path, weights, out_path):
        resnet = xrv.models.ResNet
        model = resnet(weights="resnet50-res512-all", weights_filename_local=weights)

        preds = []
        data = XRVDataset(data_path)
        resize = Resize(512)
        with torch.no_grad():
            for sample in tqdm(data):
                img = resize(torch.from_numpy(sample["img"]).unsqueeze(0))
                out = model(img)
                preds.append([sample["Path"]] + out.tolist()[0])

        pred_cols = ["Path"] + model.pathologies
        preds_df = pd.DataFrame(data=preds, columns=pred_cols)
        preds_df.to_csv(out_path, index=False)


@app.command("infer")
def infer(
    data_path: str = typer.Option(..., "--data_path"),
    weights: str = typer.Option(..., "--weights"),
    out_path: str = typer.Option(..., "--out_path"),
):
    XRVInference.run(data_path, weights, out_path)


if __name__ == "__main__":
    app()
