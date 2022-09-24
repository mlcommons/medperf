import glob
import numpy as np
import os
import torch
from model import RSTN


def coarse_testing(imgs_path, output_path, ckpt_path, device, plane, params):

    crop_margin = params["crop_margin"]
    crop_prob = params["crop_prob"]
    crop_sample_batch = params["crop_sample_batch"]
    low_range = params["low_range"]
    high_range = params["high_range"]
    slice_thickness = params["slice_thickness"]

    net = RSTN(
        crop_margin=crop_margin,
        crop_prob=crop_prob,
        crop_sample_batch=crop_sample_batch,
        TEST="C",
    )
    if device == "cuda":
        net = net.cuda()
        net.load_state_dict(torch.load(ckpt_path))
    else:
        net = net.cpu()
        net.load_state_dict(torch.load(ckpt_path, map_location=torch.device("cpu")))
    net.eval()

    images = list(glob.iglob(os.path.join(imgs_path, "*.npy")))
    images.sort()
    for i, image_path in enumerate(images):
        print("Running coarse inference:", i + 1, "/", len(images))
        name = os.path.basename(image_path)
        pred_path = os.path.join(output_path, name.replace(".npy", ".npz"))
        image = np.load(image_path).astype(np.float32)
        np.minimum(np.maximum(image, low_range, image), high_range, image)
        image -= low_range
        image /= high_range - low_range
        pred = np.zeros(image.shape, dtype=np.float32)
        minR = 0
        if plane == "X":
            maxR = image.shape[0]
        elif plane == "Y":
            maxR = image.shape[1]
        elif plane == "Z":
            maxR = image.shape[2]
        for j in range(minR, maxR):
            if slice_thickness == 1:
                sID = [j, j, j]
            elif slice_thickness == 3:
                sID = [max(minR, j - 1), j, min(maxR - 1, j + 1)]
            if plane == "X":
                image_ = image[sID, :, :].astype(np.float32)
            elif plane == "Y":
                image_ = image[:, sID, :].transpose(1, 0, 2).astype(np.float32)
            elif plane == "Z":
                image_ = image[:, :, sID].transpose(2, 0, 1).astype(np.float32)

            image_ = image_.reshape((1, 3, image_.shape[1], image_.shape[2]))
            if device == "cuda":
                image_ = torch.from_numpy(image_).cuda().float()
            else:
                image_ = torch.from_numpy(image_).cpu().float()

            out = net(image_).data.cpu().numpy()[0, :, :, :]

            if slice_thickness == 1:
                if plane == "X":
                    pred[j, :, :] = out
                elif plane == "Y":
                    pred[:, j, :] = out
                elif plane == "Z":
                    pred[:, :, j] = out
            elif slice_thickness == 3:
                if plane == "X":
                    if j == minR:
                        pred[j : j + 2, :, :] += out[1:3, :, :]
                    elif j == maxR - 1:
                        pred[j - 1 : j + 1, :, :] += out[0:2, :, :]
                    else:
                        pred[j - 1 : j + 2, :, :] += out[...]
                elif plane == "Y":
                    if j == minR:
                        pred[:, j : j + 2, :] += out[1:3, :, :].transpose(1, 0, 2)
                    elif j == maxR - 1:
                        pred[:, j - 1 : j + 1, :] += out[0:2, :, :].transpose(1, 0, 2)
                    else:
                        pred[:, j - 1 : j + 2, :] += out[...].transpose(1, 0, 2)
                elif plane == "Z":
                    if j == minR:
                        pred[:, :, j : j + 2] += out[1:3, :, :].transpose(1, 2, 0)
                    elif j == maxR - 1:
                        pred[:, :, j - 1 : j + 1] += out[0:2, :, :].transpose(1, 2, 0)
                    else:
                        pred[:, :, j - 1 : j + 2] += out[...].transpose(1, 2, 0)
        if slice_thickness == 3:
            if plane == "X":
                pred[minR, :, :] /= 2
                pred[minR + 1 : maxR - 1, :, :] /= 3
                pred[maxR - 1, :, :] /= 2
            elif plane == "Y":
                pred[:, minR, :] /= 2
                pred[:, minR + 1 : maxR - 1, :] /= 3
                pred[:, maxR - 1, :] /= 2
            elif plane == "Z":
                pred[:, :, minR] /= 2
                pred[:, :, minR + 1 : maxR - 1] /= 3
                pred[:, :, maxR - 1] /= 2
        pred = np.around(pred * 255).astype(np.uint8)
        np.savez_compressed(pred_path, volume=pred)
