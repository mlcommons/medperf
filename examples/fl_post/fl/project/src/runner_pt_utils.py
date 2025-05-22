# Copyright (C) 2020-2023 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Utilities modeule for PyTorch related Task Runners"""

# NOTE: this might want to be its own PR to openfl

from copy import deepcopy
import torch as pt
import numpy as np

from openfl.utilities.split import split_tensor_dict_for_holdouts
from openfl.utilities import TensorKey


def rebuild_model_util(runner_class, input_tensor_dict, testing_with_opt_setting=False, **kwargs):
        """
        Parse tensor names and update weights of model. Assumes opt_treatement == CONTINUE_LOCAL, but
        allows for writing in optimizer variables for testing purposes

        Returns:
            None
        """
        if testing_with_opt_setting:
            with_opt_vars = True
        else:
            with_opt_vars = False

        runner_class.set_tensor_dict(input_tensor_dict, with_opt_vars=with_opt_vars)


def derive_opt_state_dict(opt_state_dict):
    """Separate optimizer tensors from the tensor dictionary.

    Flattens the optimizer state dict so as to have key, value pairs with
    values as numpy arrays.
    The keys have sufficient info to restore opt_state_dict using
    expand_derived_opt_state_dict.

    Args:
        opt_state_dict: The optimizer state dictionary

    """
    derived_opt_state_dict = {}

    # Determine if state is needed for this optimizer.
    if len(opt_state_dict['state']) == 0:
        derived_opt_state_dict['__opt_state_needed'] = 'false'
        return derived_opt_state_dict

    derived_opt_state_dict['__opt_state_needed'] = 'true'

    # Using one example state key, we collect keys for the corresponding
    # dictionary value.
    example_state_key = opt_state_dict['param_groups'][0]['params'][0]
    example_state_subkeys = set(
        opt_state_dict['state'][example_state_key].keys()
    )

    

    # We assume that the state collected for all params in all param groups is
    # the same.
    # We also assume that whether or not the associated values to these state
    # subkeys is a tensor depends only on the subkey.
    # Using assert statements to break the routine if these assumptions are
    # incorrect.
    for state_key in opt_state_dict['state'].keys():
        assert example_state_subkeys == set(opt_state_dict['state'][state_key].keys())
        for state_subkey in example_state_subkeys:
            assert (isinstance(
                opt_state_dict['state'][example_state_key][state_subkey],
                pt.Tensor)
                == isinstance(
                    opt_state_dict['state'][state_key][state_subkey],
                    pt.Tensor))

    state_subkeys = list(opt_state_dict['state'][example_state_key].keys())

    # Tags will record whether the value associated to the subkey is a
    # tensor or not.
    state_subkey_tags = []
    for state_subkey in state_subkeys:
        if isinstance(
                opt_state_dict['state'][example_state_key][state_subkey],
                pt.Tensor
        ):
            state_subkey_tags.append('istensor')
        else:
            state_subkey_tags.append('')
    state_subkeys_and_tags = list(zip(state_subkeys, state_subkey_tags))
    
    # Forming the flattened dict, using a concatenation of group index,
    # subindex, tag, and subkey inserted into the flattened dict key -
    # needed for reconstruction.
    nb_params_per_group = []
    for group_idx, group in enumerate(opt_state_dict['param_groups']):
        for idx, param_id in enumerate(group['params']):
            for subkey, tag in state_subkeys_and_tags:
                if tag == 'istensor':
                    new_v = opt_state_dict['state'][param_id][
                        subkey].cpu().numpy()
                else:
                    new_v = np.array(
                        [opt_state_dict['state'][param_id][subkey]]
                    )
                derived_opt_state_dict[f'__opt_state_{group_idx}_{idx}_{tag}_{subkey}'] = new_v
        nb_params_per_group.append(idx + 1)
    # group lengths are also helpful for reconstructing
    # original opt_state_dict structure
    derived_opt_state_dict['__opt_group_lengths'] = np.array(
        nb_params_per_group
    )
    return derived_opt_state_dict


def expand_derived_opt_state_dict(derived_opt_state_dict, device):
    """Expand the optimizer state dictionary.

    Takes a derived opt_state_dict and creates an opt_state_dict suitable as
    input for load_state_dict for restoring optimizer state.

    Reconstructing state_subkeys_and_tags using the example key
    prefix, "__opt_state_0_0_", certain to be present.

    Args:
        derived_opt_state_dict: Optimizer state dictionary

    Returns:
        dict: Optimizer state dictionary
    """
    state_subkeys_and_tags = []
    for key in derived_opt_state_dict:
        if key.startswith('__opt_state_0_0_'):
            stripped_key = key[16:]
            if stripped_key.startswith('istensor_'):
                this_tag = 'istensor'
                subkey = stripped_key[9:]
            else:
                this_tag = ''
                subkey = stripped_key[1:]
            state_subkeys_and_tags.append((subkey, this_tag))

    opt_state_dict = {'param_groups': [], 'state': {}}
    nb_params_per_group = list(
        derived_opt_state_dict.pop('__opt_group_lengths').astype(np.int32)
    )

    # Construct the expanded dict.
    for group_idx, nb_params in enumerate(nb_params_per_group):
        these_group_ids = [f'{group_idx}_{idx}' for idx in range(nb_params)]
        opt_state_dict['param_groups'].append({'params': these_group_ids})
        for this_id in these_group_ids:
            opt_state_dict['state'][this_id] = {}
            for subkey, tag in state_subkeys_and_tags:
                flat_key = f'__opt_state_{this_id}_{tag}_{subkey}'
                if tag == 'istensor':
                    new_v = pt.from_numpy(derived_opt_state_dict.pop(flat_key))
                else:
                    # Here (for currrently supported optimizers) the subkey
                    # should be 'step' and the length of array should be one.
                    assert subkey == 'step'
                    assert len(derived_opt_state_dict[flat_key]) == 1
                    new_v = int(derived_opt_state_dict.pop(flat_key))
                opt_state_dict['state'][this_id][subkey] = new_v

    # sanity check that we did not miss any optimizer state (after removing __opt_state_needed)
    derived_opt_state_dict.pop('__opt_state_needed')
    if len(derived_opt_state_dict) != 0:
        raise ValueError(f"Opt state should have been exausted, but we have left: {derived_opt_state_dict}")

    return opt_state_dict


def initialize_tensorkeys_for_functions_util(runner_class, with_opt_vars=False):
        """Set the required tensors for all publicly accessible task methods.

        By default, this is just all of the layers and optimizer of the model.
        Custom tensors should be added to this function.

        Args:
            None

        Returns:
            None
        """
        # TODO there should be a way to programmatically iterate through
        #  all of the methods in the class and declare the tensors.
        # For now this is done manually

        output_model_dict = runner_class.get_tensor_dict(with_opt_vars=with_opt_vars)
        global_model_dict, local_model_dict = split_tensor_dict_for_holdouts(
            runner_class.logger, output_model_dict,
            **runner_class.tensor_dict_split_fn_kwargs
        )
        if not with_opt_vars:
            global_model_dict_val = global_model_dict
            local_model_dict_val = local_model_dict
        else:
            output_model_dict = runner_class.get_tensor_dict(with_opt_vars=False)
            global_model_dict_val, local_model_dict_val = split_tensor_dict_for_holdouts(
                runner_class.logger,
                output_model_dict,
                **runner_class.tensor_dict_split_fn_kwargs
            )

        runner_class.required_tensorkeys_for_function['train_batches'] = [
            TensorKey(tensor_name, 'GLOBAL', 0, False, ('model',))
            for tensor_name in global_model_dict]
        runner_class.required_tensorkeys_for_function['train_batches'] += [
            TensorKey(tensor_name, 'LOCAL', 0, False, ('model',))
            for tensor_name in local_model_dict]

        runner_class.required_tensorkeys_for_function['train'] = [
            TensorKey(
                tensor_name, 'GLOBAL', 0, False, ('model',)
            ) for tensor_name in global_model_dict
        ]
        runner_class.required_tensorkeys_for_function['train'] += [
            TensorKey(
                tensor_name, 'LOCAL', 0, False, ('model',)
            ) for tensor_name in local_model_dict
        ]

        # Validation may be performed on local or aggregated (global) model,
        # so there is an extra lookup dimension for kwargs
        runner_class.required_tensorkeys_for_function['validate'] = {}
        # TODO This is not stateless. The optimizer will not be
        runner_class.required_tensorkeys_for_function['validate']['apply=local'] = [
            TensorKey(tensor_name, 'LOCAL', 0, False, ('trained',))
            for tensor_name in {
                **global_model_dict_val,
                **local_model_dict_val
            }]
        runner_class.required_tensorkeys_for_function['validate']['apply=global'] = [
            TensorKey(tensor_name, 'GLOBAL', 0, False, ('model',))
            for tensor_name in global_model_dict_val
        ]
        runner_class.required_tensorkeys_for_function['validate']['apply=global'] += [
            TensorKey(tensor_name, 'LOCAL', 0, False, ('model',))
            for tensor_name in local_model_dict_val
        ] 


def to_cpu_numpy(state):
    """Send data to CPU as Numpy array.

    Args:
        state

    """
    # deep copy so as to decouple from active model
    state = deepcopy(state)

    for k, v in state.items():
        # When restoring, we currently assume all values are tensors.
        if not pt.is_tensor(v):
            raise ValueError('We do not currently support non-tensors '
                             'coming from model.state_dict()')
        # get as a numpy array, making sure is on cpu
        state[k] = v.cpu().numpy()
    return state


class DummyDataLoader():
    def __init__(self, feature_shape, training_data_size, valid_data_size):
        self.feature_shape = feature_shape
        self.training_data_size = training_data_size
        self.valid_data_size = valid_data_size

    def get_feature_shape(self):
        return self.feature_shape
    
    def get_training_data_size(self):
        return self.training_data_size
    
    def get_valid_data_size(self):
        return self.valid_data_size
