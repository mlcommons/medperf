import glob
import os
import torch
from coarse_testing import coarse_testing
from coarse2fine_testing import coarse2fine_testing


def run_inference(images_path, output_path, ckpts_path, params):
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"

    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda"

    ckpts = list(glob.iglob(os.path.join(ckpts_path, "*.pkl")))
    assert len(ckpts) == 3, "must have 3 checkpoints each for each plane XYZ"
    # Assuming X,Y,Z are the way to know which ckpt is which
    ckpts = {plane: [ckpt for ckpt in ckpts if plane in ckpt] for plane in "XYZ"}
    for ckpt in ckpts.values():
        assert len(ckpt) == 1
    ckpts = {key: val[0] for key, val in ckpts.items()}

    for plane in "XYZ":
        plane_out_path = os.path.join(output_path, "coarse", plane)
        os.makedirs(plane_out_path, exist_ok=True)
        coarse_testing(images_path, plane_out_path, ckpts[plane], device, plane, params)

    coarse2fine_testing(images_path, output_path, ckpts, device, params)
