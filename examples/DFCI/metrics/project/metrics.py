import glob
import os
import numpy as np
from utils import DSC_computation
import yaml


def coarse_metrics(preds_path, labels_path):

    metrics_dict = {}

    labels = list(glob.iglob(os.path.join(labels_path, "*.npy")))
    labels.sort()

    for plane in "XYZ":
        metrics_dict[plane] = {}
        DSC = np.zeros([len(labels)])
        for i, label_path in enumerate(labels):
            name = os.path.basename(label_path)
            pred = os.path.join(preds_path, plane, name.replace(".npy", ".npz"))
            pred = np.load(pred)["volume"]
            pred_temp = pred >= 128
            label = np.load(label_path).astype(np.uint8)
            DSC[i], inter_sum, pred_sum, label_sum = DSC_computation(label, pred_temp)
            if pred_sum == 0 and label_sum == 0:
                DSC[i] = 0

            metrics_dict[plane][name] = DSC[i].tolist()

        metrics_dict[plane]["avg"] = np.mean(DSC).tolist()

    return metrics_dict


def fine_metrics(preds_path, labels_path, max_rounds):

    metrics_dict = {}

    labels = list(glob.iglob(os.path.join(labels_path, "*.npy")))
    labels.sort()

    DSC = np.zeros((max_rounds + 1, len(labels)))
    DSC_90 = np.zeros((len(labels)))
    DSC_95 = np.zeros((len(labels)))
    DSC_98 = np.zeros((len(labels)))
    DSC_99 = np.zeros((len(labels)))
    for i, label_path in enumerate(labels):
        label = np.load(label_path).astype(np.uint8)
        name = os.path.basename(label_path)
        for r in range(max_rounds + 1):
            pred = os.path.join(preds_path, name.replace(".npy", ""), f"round_{r}.npz")
            pred = np.load(pred)["volume"]

            DSC[r, i], inter_sum, pred_sum, label_sum = DSC_computation(label, pred)

            if pred_sum == 0 and label_sum == 0:
                DSC[r, i] = 0

            if r > 0:
                inter_DSC, inter_sum, pred_sum, label_sum = DSC_computation(
                    mask, pred
                )  # mask is prev pred
                if pred_sum == 0 and label_sum == 0:
                    inter_DSC = 1

                if DSC_90[i] == 0 and (r == max_rounds or inter_DSC >= 0.90):
                    DSC_90[i] = DSC[r, i]
                if DSC_95[i] == 0 and (r == max_rounds or inter_DSC >= 0.95):
                    DSC_95[i] = DSC[r, i]
                if DSC_98[i] == 0 and (r == max_rounds or inter_DSC >= 0.98):
                    DSC_98[i] = DSC[r, i]
                if DSC_99[i] == 0 and (r == max_rounds or inter_DSC >= 0.99):
                    DSC_99[i] = DSC[r, i]

            mask = pred

        metrics_dict[name] = DSC[-1, i].tolist()

    metrics_dict["avg"] = np.mean(DSC[-1, :]).tolist()

    metrics_dict["DSC_90"] = np.mean(DSC_90).tolist()
    metrics_dict["DSC_95"] = np.mean(DSC_95).tolist()
    metrics_dict["DSC_98"] = np.mean(DSC_98).tolist()
    metrics_dict["DSC_99"] = np.mean(DSC_99).tolist()

    return metrics_dict


def metrics(preds_path, labels_path, params_file, out_path):
    with open(params_file, "r") as f:
        params = yaml.full_load(f)

    coarse = coarse_metrics(os.path.join(preds_path, "coarse"), labels_path)
    fine = fine_metrics(os.path.join(preds_path, "fine"), labels_path, params["max_rounds"])

    with open(out_path, "w") as f:
        yaml.dump({"DSC": {"coarse": coarse, "fine": fine}}, f)
