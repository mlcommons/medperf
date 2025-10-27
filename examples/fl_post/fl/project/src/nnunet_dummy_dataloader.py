# Copyright (C) 2020-2021 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Contributors: Micah Sheller, Brandon Edwards

"""

"""You may copy this file as the starting point of your own model."""

import json
import os


class NNUNetDummyDataLoader:
    def __init__(self, data_path, p_train):
        self.task_name = data_path
        data_base_path = os.path.join(os.environ["nnUNet_preprocessed"], self.task_name)
        with open(f"{data_base_path}/dataset.json", "r") as f:
            data_config = json.load(f)
        data_size = data_config["numTraining"]

        # TODO: determine how nnunet validation splits round
        self.train_data_size = int(p_train * data_size)
        self.valid_data_size = data_size - self.train_data_size

    def get_feature_shape(self):
        return [1, 1, 1]

    def get_train_data_size(self):
        return self.train_data_size

    def get_valid_data_size(self):
        return self.valid_data_size

    def get_task_name(self):
        return self.task_name
