# Copyright (C) 2020-2021 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Contributors: Micah Sheller, Brandon Edwards

"""

"""You may copy this file as the starting point of your own model."""

import json
import os

class NNUNetDummyDataLoader():
    def __init__(self, data_path, p_train, partial_epoch=1.0):
        self.task_name = data_path
        data_base_path = os.path.join(os.environ['nnUNet_preprocessed'], self.task_name)
        with open(f'{data_base_path}/dataset.json', 'r') as f:
            data_config = json.load(f)
        data_size = data_config['numTraining']

        # NOTE: Intended use with PyTorchNNUNetCheckpointTaskRunner where partial_epoch scales down num_train_batches_per_epoch 
        # and num_val_batches_per_epoch. NNUnet loaders sample batches with replacement. Ignoring rounding (int()),
        # the 'data sizes' below are divided by batch_size to obtain the number of batches used per epoch.
        # These 'data sizes' therefore establish correct relative weights for train and val result aggregation over collaboarators
        # due to the fact that batch_size is equal across all collaborators. In addition, over many rounds each data point
        # at a particular collaborator informs the results with equal measure. In particular, the average number of times (over 
        # repeated runs of the federation) that a particular sample is used for a training or val result
        # over the corse of the whole federation is given by the 'data sizes' below.
        # TODO: determine how nnunet validation splits round
        self.train_data_size = int(partial_epoch * p_train * data_size)
        self.valid_data_size = int(partial_epoch * (1 - p_train) * data_size)

    def get_feature_shape(self):
        return [1,1,1]
    
    def get_train_data_size(self):
        return self.train_data_size
    
    def get_valid_data_size(self):
        return self.valid_data_size
    
    def get_task_name(self):
        return self.task_name
