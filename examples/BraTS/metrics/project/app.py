# Code adapted from https://github.com/Sage-Bionetworks-Challenges/brats-dream-challenge-infra/blob/main/Docker/score.py

from pathlib import Path
from typing import Dict, Union
import re
import yaml
import os
import subprocess

from loguru import logger
import numpy as np
import pandas as pd
from sklearn.metrics import multilabel_confusion_matrix
import SimpleITK as sitk


BRATS_REGIONS = {"WT": (1, 2, 4), "TC": (1, 4), "ET": (4,)}


def to_brats_regions(label_mask: np.ndarray) -> np.ndarray:
    # converts BraTS labels to regions. Input shape: XYZ; output: XYZC
    region_masks = []
    for region_labels in BRATS_REGIONS.values():
        mask_new = np.zeros_like(label_mask, dtype=np.uint8)
        for l in region_labels:
            mask_new[label_mask == l] = 1
        region_masks.append(mask_new)
    return np.stack(region_masks, axis=-1)


def load_scan(filepath: Path) -> np.ndarray:
    image = sitk.GetArrayFromImage(sitk.ReadImage(str(filepath.absolute())))
    image = to_brats_regions(image)
    return image


def compute_confusion_matrix(y_pred: np.ndarray, y_true: np.ndarray) -> Dict[str, int]:
    # flatten spatial dims
    if len(y_pred.shape) > 2:
        y_pred = y_pred.reshape((-1, len(BRATS_REGIONS)))
    if len(y_true.shape) > 2:
        y_true = y_true.reshape((-1, len(BRATS_REGIONS)))
    confmat = multilabel_confusion_matrix(y_true=y_true, y_pred=y_pred)
    results = {}
    for i, region in enumerate(BRATS_REGIONS):
        results[f"TN_{region}"] = confmat[i, 0, 0]
        results[f"FN_{region}"] = confmat[i, 1, 0]
        results[f"TP_{region}"] = confmat[i, 1, 1]
        results[f"FP_{region}"] = confmat[i, 0, 1]
    return results


def run_captk(pred, gold, tmp):
    """
    Run BraTS Similarity Metrics computation of prediction scan
    against goldstandard.
    """
    cmd = [
        os.path.join("/work/CaPTk/bin/Utilities"),
        "-i",
        gold,
        "-lsb",
        pred,
        "-o",
        tmp,
    ]
    subprocess.check_call(cmd)


def extract_metrics(tmp, subject_id):
    """Get scores for three regions: ET, WT, and TC.
    Metrics wanted:
      - Dice score
      - Hausdorff distance
      - specificity
      - sensitivity
      - precision
    """
    res = (
        pd.read_csv(tmp, index_col="Labels")
        .filter(
            items=[
                "Labels",
                "Dice",
                "Hausdorff95",
                "Sensitivity",
                "Specificity",
                "Precision",
            ]
        )
        .filter(items=["ET", "WT", "TC"], axis=0)
        .reset_index()
        .assign(subject_id=subject_id)
        .pivot(index="subject_id", columns="Labels")
    )
    res.columns = ["_".join(col).strip() for col in res.columns]
    return res


def score(labels_dir: Path, preds_dir: Path, tmp_output="tmp.csv") -> pd.DataFrame:
    """Compute and return scores for each scan."""
    scores = []
    missing_preds = []
    for label_path in labels_dir.iterdir():
        if not label_path.is_file():
            logger.warning(f"Skipped directory {label_path}")
            continue
        subject_id = re.findall(r"(\w+)_final_seg\.nii\.gz", label_path.name)[0]
        logger.info(f"Processing {subject_id}...")

        pred_path = preds_dir / (subject_id + ".nii.gz")
        if not pred_path.exists():
            missing_preds.append(subject_id)

        try:
            run_captk(str(pred_path.absolute()), str(label_path.absolute()), tmp_output)
        except subprocess.CalledProcessError:
            # If no output found, give penalized scores.
            scan_scores = pd.DataFrame(
                {
                    "subject_id": [subject_id],
                    "Dice_ET": [0],
                    "Dice_TC": [0],
                    "Dice_WT": [0],
                    "Hausdorff95_ET": [374],
                    "Hausdorff95_TC": [374],
                    "Hausdorff95_WT": [374],
                    "Sensitivity_ET": [0],
                    "Sensitivity_TC": [0],
                    "Sensitivity_WT": [0],
                    "Specificity_ET": [0],
                    "Specificity_TC": [0],
                    "Specificity_WT": [0],
                    "Precision_ET": [0],
                    "Precision_TC": [0],
                    "Precision_WT": [0],
                    "TP_ET": [0],
                    "TP_TC": [0],
                    "TP_WT": [0],
                    "FP_ET": [0],
                    "FP_TC": [0],
                    "FP_WT": [0],
                    "TN_ET": [0],
                    "TN_TC": [0],
                    "TN_WT": [0],
                    "FN_ET": [240 * 240 * 155],
                    "FN_TC": [240 * 240 * 155],
                    "FN_WT": [240 * 240 * 155],
                }
            ).set_index("subject_id")
        else:
            scan_scores = extract_metrics(tmp_output, subject_id)
            os.remove(tmp_output)  # Remove file, as it's no longer needed

            confusion_matrix = compute_confusion_matrix(
                load_scan(pred_path), load_scan(label_path)
            )
            confusion_matrix["subject_id"] = subject_id
            extra_scores = pd.DataFrame([confusion_matrix]).set_index("subject_id")
            scan_scores = pd.concat([scan_scores, extra_scores], axis=1)

        scores.append(scan_scores)
    if len(missing_preds) > 0:
        logger.warning(
            f"Warning: In total, {len(missing_preds)} predictions were missing. "
            f"Here is the list: {missing_preds}"
        )
    return pd.concat(scores).sort_values(by="subject_id")


def evaluate(
    label_dir: Union[str, Path],
    prediction_dir: Union[str, Path],
    output_file: Union[str, Path],
    log_file: Union[str, Path],
) -> None:
    logger.add(log_file)
    results = score(Path(label_dir), Path(prediction_dir))

    results_dict = results.to_dict(orient="index")

    with open(output_file, "w") as f:
        yaml.dump(results_dict, f)
    logger.info(f"Results saved at {output_file}")
