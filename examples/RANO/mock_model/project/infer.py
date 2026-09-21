"""Minimal placeholder reference model for the RANO benchmark.

Does no real inference. For every ``<subject>/<timepoint>`` folder found under
``data_path`` (the shape the prep-workflow RANO preparator emits — brain-extracted
MRI volumes named ``<subject>_<timepoint>_brain_<modality>.nii.gz``), it writes an
all-background segmentation volume with the same shape/affine as one of the input
volumes, named the way ``mlcommons/rano-metrics`` expects raw predictions to be
named: ``<subject>_<timepoint with dots replaced by underscores>.nii.gz`` — see
``examples/cc/rano/implementation/benchmark/metrics/utils.py``'s
``symlink_one_subject``, which symlinks the real ``..._final_seg.nii.gz`` ground
truth under that same transformed name before comparing.

This exists only to exercise the MedPerf benchmark-registration and
compatibility-test plumbing against real prepared RANO data without needing a
trained (and GPU/CUDA-dependent) segmentation model. It is not a real reference
model: every prediction is empty, so metrics computed against it are meaningless.
"""

import os

import nibabel as nib
import numpy as np

DATA_DIR = os.environ.get("DATA_DIR", "/mlcommons/volumes/data")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/mlcommons/volumes/predictions")


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    written = 0

    for subject in sorted(os.listdir(DATA_DIR)):
        subject_path = os.path.join(DATA_DIR, subject)
        if not os.path.isdir(subject_path):
            continue
        for timepoint in sorted(os.listdir(subject_path)):
            tp_path = os.path.join(subject_path, timepoint)
            if not os.path.isdir(tp_path):
                continue

            volumes = sorted(f for f in os.listdir(tp_path) if f.endswith(".nii.gz"))
            if not volumes:
                print(f"skipping {subject}/{timepoint}: no .nii.gz volumes found")
                continue

            ref = nib.load(os.path.join(tp_path, volumes[0]))
            blank = np.zeros(ref.shape, dtype=np.uint8)
            pred = nib.Nifti1Image(blank, ref.affine, ref.header)

            out_name = f"{subject}_{timepoint.replace('.', '_')}.nii.gz"
            nib.save(pred, os.path.join(OUTPUT_DIR, out_name))
            print(f"wrote placeholder prediction: {out_name} (shape={ref.shape})")
            written += 1

    print(f"done: {written} placeholder prediction(s) written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
