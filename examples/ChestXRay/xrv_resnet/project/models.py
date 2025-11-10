from collections import OrderedDict

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
import urllib
import pathlib
import os
import sys
import requests
import numpy as np
import warnings

warnings.filterwarnings("ignore")
from torchxrayvision.models import model_urls


class ResNet(nn.Module):
    def __init__(
        self, weights=None, apply_sigmoid=False, weights_filename_local=None,
    ):
        super(ResNet, self).__init__()

        self.apply_sigmoid = apply_sigmoid
        self.weights = weights
        self.weights_filename_local = weights_filename_local

        if not self.weights in model_urls.keys():
            possible_weights = [k for k in model_urls.keys() if k.startswith("resnet")]
            raise Exception("Weights value must be in {}".format(possible_weights))

        self.weights_dict = model_urls[weights]
        self.pathologies = model_urls[weights]["labels"]

        if self.weights.startswith("resnet101"):
            self.model = torchvision.models.resnet101(
                num_classes=len(self.weights_dict["labels"]), pretrained=False
            )
            # patch for single channel
            self.model.conv1 = torch.nn.Conv2d(
                1, 64, kernel_size=7, stride=2, padding=3, bias=False
            )

        elif self.weights.startswith("resnet50"):
            self.model = torchvision.models.resnet50(
                num_classes=len(self.weights_dict["labels"]), pretrained=False
            )
            # patch for single channel
            self.model.conv1 = torch.nn.Conv2d(
                1, 64, kernel_size=7, stride=2, padding=3, bias=False
            )

        try:
            self.model.load_state_dict(torch.load(self.weights_filename_local))
        except Exception as e:
            print("Loading failure. Check weights file:", self.weights_filename_local)
            raise e

        if "op_threshs" in model_urls[weights]:
            self.register_buffer(
                "op_threshs", torch.tensor(model_urls[weights]["op_threshs"])
            )

        self.upsample = nn.Upsample(
            size=(512, 512), mode="bilinear", align_corners=False
        )

        self.eval()

    def __repr__(self):
        if self.weights != None:
            return "XRV-ResNet-{}".format(self.weights)
        else:
            return "XRV-ResNet"

    def features(self, x):

        x = fix_resolution(x, 512, self)

        x = self.model.conv1(x)
        x = self.model.bn1(x)
        x = self.model.relu(x)
        x = self.model.maxpool(x)

        x = self.model.layer1(x)
        x = self.model.layer2(x)
        x = self.model.layer3(x)
        x = self.model.layer4(x)

        x = self.model.avgpool(x)
        x = torch.flatten(x, 1)
        return x

    def forward(self, x):

        x = fix_resolution(x, 512, self)

        out = self.model(x)

        if hasattr(self, "apply_sigmoid") and self.apply_sigmoid:
            out = torch.sigmoid(out)

        if hasattr(self, "op_threshs") and (self.op_threshs != None):
            out = torch.sigmoid(out)
            out = op_norm(out, self.op_threshs)
        return out


warning_log = {}


def fix_resolution(x, resolution, model):
    """
    Check resolution of input and resize to match requested
    """

    # just skip it if upsample was removed somehow
    if not hasattr(model, "upsample") or (model.upsample == None):
        return x

    if (x.shape[2] != resolution) | (x.shape[3] != resolution):
        if not hash(model) in warning_log:
            print(
                "Warning: Input size ({}x{}) is not the native resolution ({}x{}) for this model. A resize will be performed but this could impact performance.".format(
                    x.shape[2], x.shape[3], resolution, resolution
                )
            )
            warning_log[hash(model)] = True
        return model.upsample(x)
    return x


def op_norm(outputs, op_threshs):
    """normalize outputs according to operating points for a given model.
    Args: 
        outputs: outputs of self.classifier(). torch.Size(batch_size, num_tasks) 
        op_threshs_arr: torch.Size(batch_size, num_tasks) with self.op_threshs expanded.
    Returns:
        outputs_new: normalized outputs, torch.Size(batch_size, num_tasks)
    """
    # expand to batch size so we can do parallel comp
    op_threshs = op_threshs.expand(outputs.shape[0], -1)

    # initial values will be 0.5
    outputs_new = torch.zeros(outputs.shape, device=outputs.device) + 0.5

    # only select non-nan elements otherwise the gradient breaks
    mask_leq = (outputs < op_threshs) & ~torch.isnan(op_threshs)
    mask_gt = ~(outputs < op_threshs) & ~torch.isnan(op_threshs)

    # scale outputs less than thresh
    outputs_new[mask_leq] = outputs[mask_leq] / (op_threshs[mask_leq] * 2)
    # scale outputs greater than thresh
    outputs_new[mask_gt] = 1.0 - (
        (1.0 - outputs[mask_gt]) / ((1 - op_threshs[mask_gt]) * 2)
    )

    return outputs_new


def get_densenet_params(arch):
    assert "dense" in arch
    if arch == "densenet161":
        ret = dict(growth_rate=48, block_config=(6, 12, 36, 24), num_init_features=96)
    elif arch == "densenet169":
        ret = dict(growth_rate=32, block_config=(6, 12, 32, 32), num_init_features=64)
    elif arch == "densenet201":
        ret = dict(growth_rate=32, block_config=(6, 12, 48, 32), num_init_features=64)
    else:
        # default configuration: densenet121
        ret = dict(growth_rate=32, block_config=(6, 12, 24, 16), num_init_features=64)
    return ret


def get_model(weights, **kwargs):
    if weights.startswith("densenet"):
        return DenseNet(weights=weights, **kwargs)
    else:
        raise Exception("Unknown model")
