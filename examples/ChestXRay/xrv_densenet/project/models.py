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


class _DenseLayer(nn.Sequential):
    def __init__(self, num_input_features, growth_rate, bn_size, drop_rate):
        super(_DenseLayer, self).__init__()
        self.add_module("norm1", nn.BatchNorm2d(num_input_features)),
        self.add_module("relu1", nn.ReLU(inplace=True)),
        self.add_module(
            "conv1",
            nn.Conv2d(
                num_input_features,
                bn_size * growth_rate,
                kernel_size=1,
                stride=1,
                bias=False,
            ),
        ),
        self.add_module("norm2", nn.BatchNorm2d(bn_size * growth_rate)),
        self.add_module("relu2", nn.ReLU(inplace=True)),
        self.add_module(
            "conv2",
            nn.Conv2d(
                bn_size * growth_rate,
                growth_rate,
                kernel_size=3,
                stride=1,
                padding=1,
                bias=False,
            ),
        ),
        self.drop_rate = drop_rate

    def forward(self, x):
        new_features = super(_DenseLayer, self).forward(x)
        if self.drop_rate > 0:
            new_features = F.dropout(
                new_features, p=self.drop_rate, training=self.training
            )
        return torch.cat([x, new_features], 1)


class _DenseBlock(nn.Sequential):
    def __init__(self, num_layers, num_input_features, bn_size, growth_rate, drop_rate):
        super(_DenseBlock, self).__init__()
        for i in range(num_layers):
            layer = _DenseLayer(
                num_input_features + i * growth_rate, growth_rate, bn_size, drop_rate
            )
            self.add_module("denselayer%d" % (i + 1), layer)


class _Transition(nn.Sequential):
    def __init__(self, num_input_features, num_output_features):
        super(_Transition, self).__init__()
        self.add_module("norm", nn.BatchNorm2d(num_input_features))
        self.add_module("relu", nn.ReLU(inplace=True))
        self.add_module(
            "conv",
            nn.Conv2d(
                num_input_features,
                num_output_features,
                kernel_size=1,
                stride=1,
                bias=False,
            ),
        )
        self.add_module("pool", nn.AvgPool2d(kernel_size=2, stride=2))


class DenseNet(nn.Module):
    r"""Densenet-BC model class, based on
    `"Densely Connected Convolutional Networks" <https://arxiv.org/pdf/1608.06993.pdf>`_
    Modified from torchvision to have a variable number of input channels
    Args:
        growth_rate (int) - how many filters to add each layer (`k` in paper)
        block_config (list of 4 ints) - how many layers in each pooling block
        num_init_features (int) - the number of filters to learn in the first convolution layer
        bn_size (int) - multiplicative factor for number of bottle neck layers
          (i.e. bn_size * k features in the bottleneck layer)
        drop_rate (float) - dropout rate after each dense layer
        num_classes (int) - number of classification classes
    """

    def __init__(
        self,
        growth_rate=32,
        block_config=(6, 12, 24, 16),
        num_init_features=64,
        bn_size=4,
        drop_rate=0,
        num_classes=18,
        in_channels=1,
        weights=None,
        weights_filename_local=None,
        op_threshs=None,
        apply_sigmoid=False,
    ):

        super(DenseNet, self).__init__()

        self.apply_sigmoid = apply_sigmoid
        self.weights = weights
        self.weights_filename_local = weights_filename_local

        if self.weights != None:
            if not self.weights in model_urls.keys():
                raise Exception(
                    "weights value must be in {}".format(list(model_urls.keys()))
                )

            # set to be what this model is trained to predict
            self.pathologies = model_urls[weights]["labels"]
            num_classes = len(self.pathologies)

        # First convolution
        self.features = nn.Sequential(
            OrderedDict(
                [
                    (
                        "conv0",
                        nn.Conv2d(
                            in_channels,
                            num_init_features,
                            kernel_size=7,
                            stride=2,
                            padding=3,
                            bias=False,
                        ),
                    ),
                    ("norm0", nn.BatchNorm2d(num_init_features)),
                    ("relu0", nn.ReLU(inplace=True)),
                    ("pool0", nn.MaxPool2d(kernel_size=3, stride=2, padding=1)),
                ]
            )
        )

        # Each denseblock
        num_features = num_init_features
        for i, num_layers in enumerate(block_config):
            block = _DenseBlock(
                num_layers=num_layers,
                num_input_features=num_features,
                bn_size=bn_size,
                growth_rate=growth_rate,
                drop_rate=drop_rate,
            )
            self.features.add_module("denseblock%d" % (i + 1), block)
            num_features = num_features + num_layers * growth_rate
            if i != len(block_config) - 1:
                trans = _Transition(
                    num_input_features=num_features,
                    num_output_features=num_features // 2,
                )
                self.features.add_module("transition%d" % (i + 1), trans)
                num_features = num_features // 2

        # Final batch norm
        self.features.add_module("norm5", nn.BatchNorm2d(num_features))

        # Linear layer
        self.classifier = nn.Linear(num_features, num_classes)

        # Official init from torch repo.
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.constant_(m.bias, 0)

        # needs to be register_buffer here so it will go to cuda/cpu easily
        self.register_buffer("op_threshs", op_threshs)

        if self.weights != None:
            try:
                savedmodel = torch.load(self.weights_filename_local, map_location="cpu")
                # patch to load old models https://github.com/pytorch/pytorch/issues/42242
                for mod in savedmodel.modules():
                    if not hasattr(mod, "_non_persistent_buffers_set"):
                        mod._non_persistent_buffers_set = set()

                self.load_state_dict(savedmodel.state_dict())
            except Exception as e:
                print("Loading failure. Check weights file:", weights_filename_local)
                raise e

            self.eval()

            if "op_threshs" in model_urls[weights]:
                self.op_threshs = torch.tensor(model_urls[weights]["op_threshs"])

            self.upsample = nn.Upsample(
                size=(224, 224), mode="bilinear", align_corners=False
            )

    def __repr__(self):
        if self.weights != None:
            return "XRV-DenseNet121-{}".format(self.weights)
        else:
            return "XRV-DenseNet"

    def features2(self, x):

        x = fix_resolution(x, 224, self)

        features = self.features(x)
        out = F.relu(features, inplace=True)
        out = F.adaptive_avg_pool2d(out, (1, 1)).view(features.size(0), -1)
        return out

    def forward(self, x):

        x = fix_resolution(x, 224, self)

        features = self.features2(x)
        out = self.classifier(features)

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
