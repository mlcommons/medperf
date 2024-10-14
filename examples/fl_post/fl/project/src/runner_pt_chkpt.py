# Copyright (C) 2020-2021 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Contributors: Micah Sheller, Patrick Foley, Brandon Edwards

"""
# TODO: Clean up imports

import os
import shutil
from copy import deepcopy

import numpy as np
import torch

from openfl.utilities import TensorKey
from openfl.utilities.split import split_tensor_dict_for_holdouts

from openfl.federated.task.runner import TaskRunner
from .runner_pt_utils import rebuild_model_util, derive_opt_state_dict, expand_derived_opt_state_dict
from .runner_pt_utils import initialize_tensorkeys_for_functions_util, to_cpu_numpy


class PyTorchCheckpointTaskRunner(TaskRunner):
    """An abstract class for PyTorch model based Tasks, where training, validation etc. are processes that
       pull model state from a PyTorch checkpoint."""

    def __init__(self,
                 device = 'cuda',
                 gpu_num_string = '0',
                 checkpoint_path_initial = None,
                 checkpoint_path_save = None,
                 checkpoint_path_load = None,
                 **kwargs):
        """Initialize.

        Args:
            device(str)                 : Device ('cpu' or 'cuda') to be used for training and validation script computations.
            checkpoint_path_initial(str): Path to the model checkpoint that will be used to initialize this object and copied to the 'write' path to start.
            checkpoint_path_save(str)   : Path to the model checkpoint that will be saved and passed into the training function.
            checkpoint_path_load(str)   : Path to the model checkpoint that will be loaded. It is also the output file path for the training function.
            kwargs                      : Additional key work arguments (will be passed to rebuild_model, initialize_tensor_key_functions, TODO: <Fill this in>).
            TODO: 
        """ 
        super().__init__(**kwargs)

        self.checkpoint_path_initial = checkpoint_path_initial
        self.checkpoint_path_save    = checkpoint_path_save
        self.checkpoint_path_load    = checkpoint_path_load
        self.gpu_num_string          = gpu_num_string

        # TODO: Understand why "weights-only"

        # TODO: Both 'CONTINUE_GLOBAL' and 'RESET' could be suported here too (currently RESET throws an exception related to a 
        # missmatch in size coming from the momentum buffer and other stuff either in the model or optimizer)
        self.opt_treatment = 'CONTINUE_LOCAL'
        
        if device not in ['cpu', 'cuda']:
            raise ValueError("Device argument must be 'cpu' or 'cuda', but {device} was used instead.")
        self.device = device
        
        self.training_round_completed = False

        # enable GPUs if appropriate
        if self.device == 'cuda' and not self.gpu_num_string:
            raise ValueError(f"If device is 'cuda' then gpu_num must be set rather than allowing to be the default None.")
        else:
            os.environ['CUDA_VISIBLE_DEVICES']= self.gpu_num_string

        self.required_tensorkeys_for_function = {}
        self.initialize_tensorkeys_for_functions()

        # overwrite attribute to account for one optimizer param (in every
        # child model that does not overwrite get and set tensordict) that is
        # not a numpy array
        self.tensor_dict_split_fn_kwargs.update({
            'holdout_tensor_names': ['__opt_state_needed']
        })

        # Initialize model
        self.replace_checkpoint(self.checkpoint_path_initial)
     

    def load_checkpoint(self, checkpoint_path=None, map_location=None):
        """
        Function used to load checkpoint from disk.
        """
        if not checkpoint_path:
            checkpoint_path = self.checkpoint_path_load
        checkpoint_dict = torch.load(checkpoint_path, map_location=map_location)
        return checkpoint_dict
    
    def save_checkpoint(self, checkpoint_dict):
        """
        Function to save checkpoint to disk.
        """
        torch.save(checkpoint_dict, self.checkpoint_path_save)

    # defining some class methods using some util functions imported above

    def rebuild_model(self, input_tensor_dict, **kwargs):
        rebuild_model_util(runner_class=self, input_tensor_dict=input_tensor_dict, **kwargs)

    def initialize_tensorkeys_for_functions(self, **kwargs):
        initialize_tensorkeys_for_functions_util(runner_class=self, **kwargs)
     
    def get_required_tensorkeys_for_function(self, func_name, **kwargs):
        """
        Get the required tensors for specified function that could be called \
        as part of a task. By default, this is just all of the layers and \
        optimizer of the model.

        Args:
            func_name

        Returns:
            list : [TensorKey]
        """
        if func_name == 'validate':
            local_model = 'apply=' + str(kwargs['apply'])
            return self.required_tensorkeys_for_function[func_name][local_model]
        else:
            return self.required_tensorkeys_for_function[func_name]

    def reset_opt_vars(self):
        current_checkpoint_dict = self.load_checkpoint()
        initial_checkpoint_dict = self.load_checkpoint(checkpoint_path=self.checkpoint_path_initial)
        derived_opt_state_dict = self._get_optimizer_state(checkpoint_dict=initial_checkpoint_dict)
        self._set_optimizer_state(derived_opt_state_dict=derived_opt_state_dict, 
                                  checkpoint_dict=current_checkpoint_dict)

    def set_tensor_dict(self, tensor_dict, with_opt_vars=False):
        """Set the tensor dictionary.

        Args:
            tensor_dict: The tensor dictionary
            with_opt_vars (bool): Return the tensor dictionary including the
                                  optimizer tensors (Default=False)
        """
        return self.write_tensors_into_checkpoint(tensor_dict=tensor_dict, with_opt_vars=with_opt_vars)
    
    def replace_checkpoint(self, path_to_replacement):
        checkpoint_dict = self.load_checkpoint(checkpoint_path=path_to_replacement)
        self.save_checkpoint(checkpoint_dict)
        # shutil.copyfile(src=path_to_replacement, dst=self.checkpoint_path_save)

    def write_tensors_into_checkpoint(self, tensor_dict, with_opt_vars):
        raise NotImplementedError

    def get_tensor_dict(self, with_opt_vars=False):
        """Return the tensor dictionary.

        Args:
            with_opt_vars (bool): Return the tensor dictionary including the
                                optimizer tensors (Default=False)

        Returns:
            dict: Tensor dictionary {**dict, **optimizer_dict}

        """
        return self.read_tensors_from_checkpoint(with_opt_vars=with_opt_vars)

    def read_tensors_from_checkpoint(self, with_opt_vars):
        """Return a tensor dictionary interpreted from a checkpoint.

        Args:
            with_opt_vars (bool): Return the tensor dictionary including the
                                optimizer tensors (Default=False)

        Returns:
            dict: Tensor dictionary {**dict, **optimizer_dict}

        """
        checkpoint_dict = self.load_checkpoint()
        state = to_cpu_numpy(checkpoint_dict['state_dict'])
        if with_opt_vars:
            opt_state = self._get_optimizer_state(checkpoint_dict=checkpoint_dict)
            state = {**state, **opt_state}
        return state

    def _get_weights_names(self, with_opt_vars=False):
        """
        Gets model and potentially optimizer state dict key names
        args:
        with_opt_vars(bool) : Wether or not to get the optimizer key names 
        """
        state = self.get_tensor_dict(with_opt_vars=with_opt_vars)
        return state.keys()

    def _set_optimizer_state(self, derived_opt_state_dict, checkpoint_dict):
        """Set the optimizer state.
        # TODO: Refactor this, we will sparate the custom aspect of the checkpoint dict from the more general code 

        Args:
            derived_opt_state_dict(bool)    : flattened optimizer state dict
            checkpoint_dict(dict)           : checkpoint dictionary

        """
        self._write_optimizer_state_into_checkpoint(derived_opt_state_dict=derived_opt_state_dict,
                                              checkpoint_dict=checkpoint_dict, 
                                              checkpoint_path=self.checkpoint_out_path)
    
    def _write_optimizer_state_into_checkpoint(self, derived_opt_state_dict, checkpoint_dict, checkpoint_path):
        """Write the optimizer state contained within the derived_opt_state_dict into the checkpoint_dict,
           keeping some settings already contained within that checkpoint file the same, then write the resulting
           checkpoint back to the checkpoint path.
           TODO: Refactor this, we will separate the custom aspect of the checkpoint dict from the more general code 

        Args:
            derived_opt_state_dict(bool)    : flattened optimizer state dict
            checkpoint_dir(path)           : Path to the checkpoint file

        """
        temp_state_dict = expand_derived_opt_state_dict(derived_opt_state_dict, device=self.device)
        # Note: The expansion above only populates the 'params' key of each param group under opt_state_dict['param_groups']
        #       Therefore the default values under the additional keys such as: 'lr', 'momentum', 'dampening', 'weight_decay', 'nesterov', 'maximize', 'foreach', 'differentiable'
        #       need to be held over from the their initial values.
        # FIXME: Figure out whether or not this breaks learning rate scheduling and the like.

        # Letting default values (everything under temp_state_dict['param_groups'] except the 'params' key) 
        # stay unchanged (these are not contained in the temp_state_dict)
        # Assuming therefore that the optimizer.defaults (which hold this same info) are not changing over course of training. 
        # We only modify the 'state' key value pairs otherwise
        for group_idx, group in enumerate(temp_state_dict['param_groups']):
            checkpoint_dict['optimizer_state_dict']['param_groups'][group_idx]['params'] = group['params']
        checkpoint_dict['optimizer_state_dict']['state'] = temp_state_dict['state']

        torch.save(checkpoint_dict, checkpoint_path)

    def _get_optimizer_state(self, checkpoint_dict):
        """Get the optimizer state.
        Args:
            checkpoint_path(str)           : path to the checkpoint
        """
        return self._read_opt_state_from_checkpoint(checkpoint_dict)


    def _read_opt_state_from_checkpoint(self, checkpoint_dict):
        """Read the optimizer state from the checkpoint dict and put in tensor dict format.
        # TODO: Refactor this, we will sparate the custom aspect of the checkpoint dict from the more general code 
        """

        opt_state_dict = deepcopy(checkpoint_dict['optimizer_state_dict'])

        # Optimizer state might not have some parts representing frozen parameters
        # So we do not synchronize them
        param_keys_with_state = set(opt_state_dict['state'].keys())
        for group in opt_state_dict['param_groups']:
            local_param_set = set(group['params'])
            params_to_sync = local_param_set & param_keys_with_state
            group['params'] = sorted(params_to_sync)
        derived_opt_state_dict = derive_opt_state_dict(opt_state_dict)

        return derived_opt_state_dict


    def convert_results_to_tensorkeys(self, col_name, round_num, metrics, insert_model):
        # insert_model determined whether or not to include the model in the return dictionaries
        
        # 5. Convert to tensorkeys

        # output metric tensors (scalar)
        origin = col_name
        tags = ('trained',)
        output_metric_dict = {
            TensorKey(
                metric_name, origin, round_num, True, ('metric',)
            ): np.array(
                    metrics[metric_name]
                ) for metric_name in metrics}

        if insert_model:
            # output model tensors (Doesn't include TensorKey)
            output_model_dict = self.get_tensor_dict(with_opt_vars=True)
            global_model_dict, local_model_dict = split_tensor_dict_for_holdouts(logger=self.logger, 
                                                                                 tensor_dict=output_model_dict,
                                                                                 **self.tensor_dict_split_fn_kwargs)
        else:
            global_model_dict, local_model_dict = {}, {}

        # create global tensorkeys
        global_tensorkey_model_dict = {
            TensorKey(
                tensor_name, origin, round_num, False, tags
            ): nparray for tensor_name, nparray in global_model_dict.items()
        }
        # create tensorkeys that should stay local
        local_tensorkey_model_dict = {
            TensorKey(
                tensor_name, origin, round_num, False, tags
            ): nparray for tensor_name, nparray in local_model_dict.items()
        }
        # the train/validate aggregated function of the next round will look
        # for the updated model parameters.
        # this ensures they will be resolved locally
        next_local_tensorkey_model_dict = {
            TensorKey(
                tensor_name, origin, round_num + 1, False, ('model',)
            ): nparray for tensor_name, nparray in local_model_dict.items()
        }

        global_tensor_dict = {
            **output_metric_dict,
            **global_tensorkey_model_dict
        }
        local_tensor_dict = {
            **local_tensorkey_model_dict,
            **next_local_tensorkey_model_dict
        }

        # update the required tensors if they need to be pulled from the
        # aggregator
        # TODO this logic can break if different collaborators have different
        #  roles between rounds.
        # for example, if a collaborator only performs validation in the first
        # round but training in the second, it has no way of knowing the
        # optimizer state tensor names to request from the aggregator
        # because these are only created after training occurs.
        # A work around could involve doing a single epoch of training
        # on random data to get the optimizer names, and then throwing away
        # the model.
        if self.opt_treatment == 'CONTINUE_GLOBAL':
            self.initialize_tensorkeys_for_functions(with_opt_vars=True)

        return global_tensor_dict, local_tensor_dict
