import numpy as np
import os
import torch
from utils import post_processing
from model import RSTN
import glob


def coarse2fine_testing(imgs_path, output_path, ckpts, device, params):

    max_rounds = params["max_rounds"]
    fine_threshold = params["fine_threshold"]
    crop_margin = params["crop_margin"]
    low_range = params["low_range"]
    high_range = params["high_range"]
    slice_thickness = params["slice_thickness"]

    net_ = {}
    for plane in ["X", "Y", "Z"]:
        if device == "cuda":
            net = RSTN(crop_margin=crop_margin, TEST="F").cuda()
            net.load_state_dict(torch.load(ckpts[plane]))
        else:
            net = RSTN(crop_margin=crop_margin, TEST="F").cpu()
            net.load_state_dict(
                torch.load(ckpts[plane], map_location=torch.device("cpu"))
            )

        net.eval()
        net_[plane] = net

    images = list(glob.iglob(os.path.join(imgs_path, "*.npy")))
    images.sort()

    for i, image_path in enumerate(images):

        print("Running fine inference:", i + 1, "/", len(images))
        image = np.load(image_path).astype(np.float32)
        name = os.path.basename(image_path)
        np.minimum(np.maximum(image, low_range, image), high_range, image)
        image -= low_range
        image /= high_range - low_range
        imageX = image
        imageY = image.transpose(1, 0, 2).copy()
        imageZ = image.transpose(2, 0, 1).copy()

        for r in range(max_rounds + 1):
            print("  Iteration round " + str(r) + ":")
            pred_path = os.path.join(
                output_path, "fine", name.replace(".npy", ""), f"round_{r}.npz"
            )
            os.makedirs(os.path.split(pred_path)[0], exist_ok=True)

            if r == 0:  # coarse majority voting
                pred_ = np.zeros(image.shape, dtype=np.float32)
                for plane in ["X", "Y", "Z"]:
                    coarse_result = os.path.join(
                        output_path, "coarse", plane, name.replace(".npy", ".npz")
                    )
                    volume_data = np.load(coarse_result)
                    pred_ += volume_data["volume"]
                pred_ /= 255 * 3

            else:
                mask_sumX = np.sum(mask, axis=(1, 2))
                if mask_sumX.sum() == 0:
                    continue
                mask_sumY = np.sum(mask, axis=(0, 2))
                mask_sumZ = np.sum(mask, axis=(0, 1))
                scoreX = score
                scoreY = score.transpose(1, 0, 2).copy()
                scoreZ = score.transpose(2, 0, 1).copy()
                maskX = mask
                maskY = mask.transpose(1, 0, 2).copy()
                maskZ = mask.transpose(2, 0, 1).copy()
                pred_ = np.zeros(image.shape, dtype=np.float32)
                for plane in ["X", "Y", "Z"]:
                    net = net_[plane]
                    minR = 0
                    if plane == "X":
                        maxR = image.shape[0]
                        shape_ = (1, 3, image.shape[1], image.shape[2])
                        pred__ = np.zeros(
                            (image.shape[0], image.shape[1], image.shape[2]),
                            dtype=np.float32,
                        )
                    elif plane == "Y":
                        maxR = image.shape[1]
                        shape_ = (1, 3, image.shape[0], image.shape[2])
                        pred__ = np.zeros(
                            (image.shape[1], image.shape[0], image.shape[2]),
                            dtype=np.float32,
                        )
                    elif plane == "Z":
                        maxR = image.shape[2]
                        shape_ = (1, 3, image.shape[0], image.shape[1])
                        pred__ = np.zeros(
                            (image.shape[2], image.shape[0], image.shape[1]),
                            dtype=np.float32,
                        )
                    for j in range(minR, maxR):
                        if slice_thickness == 1:
                            sID = [j, j, j]
                        elif slice_thickness == 3:
                            sID = [max(minR, j - 1), j, min(maxR - 1, j + 1)]
                        if (
                            (plane == "X" and mask_sumX[sID].sum() == 0)
                            or (plane == "Y" and mask_sumY[sID].sum() == 0)
                            or (plane == "Z" and mask_sumZ[sID].sum() == 0)
                        ):
                            continue
                        if plane == "X":
                            image_ = imageX[sID, :, :]
                            score_ = scoreX[sID, :, :]
                            mask_ = maskX[sID, :, :]
                        elif plane == "Y":
                            image_ = imageY[sID, :, :]
                            score_ = scoreY[sID, :, :]
                            mask_ = maskY[sID, :, :]
                        elif plane == "Z":
                            image_ = imageZ[sID, :, :]
                            score_ = scoreZ[sID, :, :]
                            mask_ = maskZ[sID, :, :]

                        image_ = image_.reshape(1, 3, image_.shape[1], image_.shape[2])
                        score_ = score_.reshape(1, 3, score_.shape[1], score_.shape[2])
                        mask_ = mask_.reshape(1, 3, mask_.shape[1], mask_.shape[2])
                        if device == "cuda":
                            image_ = torch.from_numpy(image_).cuda().float()
                            score_ = torch.from_numpy(score_).cuda().float()
                            mask_ = torch.from_numpy(mask_).cuda().float()
                        else:
                            image_ = torch.from_numpy(image_).cpu().float()
                            score_ = torch.from_numpy(score_).cpu().float()
                            mask_ = torch.from_numpy(mask_).cpu().float()

                        out = (
                            net(image_, score=score_, mask=mask_)
                            .data.cpu()
                            .numpy()[0, :, :, :]
                        )

                        if slice_thickness == 1:
                            pred__[j, :, :] = out
                        elif slice_thickness == 3:
                            if j == minR:
                                pred__[minR : minR + 2, :, :] += out[1:3, :, :]
                            elif j == maxR - 1:
                                pred__[maxR - 2 : maxR, :, :] += out[0:2, :, :]
                            else:
                                pred__[j - 1 : j + 2, :, :] += out
                    if slice_thickness == 3:
                        pred__[minR, :, :] /= 2
                        pred__[minR + 1 : maxR - 1, :, :] /= 3
                        pred__[maxR - 1, :, :] /= 2
                    if plane == "X":
                        pred_ += pred__
                    elif plane == "Y":
                        pred_ += pred__.transpose(1, 0, 2)
                    elif plane == "Z":
                        pred_ += pred__.transpose(1, 2, 0)
                pred_ /= 3

            pred = (pred_ >= fine_threshold).astype(np.uint8)
            if r > 0:
                pred = post_processing(pred, pred, 0.5, 1)
            np.savez_compressed(pred_path, volume=pred)
            if r <= max_rounds:
                score = pred_  # [0,1]
                mask = pred  # {0,1} after postprocessing
