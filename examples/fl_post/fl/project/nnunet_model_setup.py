# Copyright (C) 2020-2021 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Contributors: Brandon Edwards, Micah Sheller

"""

import os
import pickle as pkl
import shutil

# from nnunet_v1 import train_nnunet


def train_on_task(task, network, network_trainer, fold, cuda_device, continue_training=False, current_epoch=0):
    os.environ['CUDA_VISIBLE_DEVICES']=cuda_device
    print(f"###########\nStarting training for task: {task}\n")
    train_nnunet(epochs=1, 
                 current_epoch = current_epoch, 
                 network = network,
                 task=task, 
                 network_trainer = network_trainer, 
                 fold=fold, 
                 continue_training=continue_training)


def model_folder(network, task, network_trainer, plans_identifier, fold, results_folder=os.environ['RESULTS_FOLDER']):
    return os.path.join(results_folder, 'nnUNet',network, task, network_trainer + '__' + plans_identifier, f'fold_{fold}')


def model_paths_from_folder(model_folder):
    return {'initial_model_path': os.path.join(model_folder, 'model_initial_checkpoint.model'), 
            'final_model_path': os.path.join(model_folder, 'model_final_checkpoint.model'),
            'initial_model_info_path': os.path.join(model_folder, 'model_initial_checkpoint.model.pkl'), 
            'final_model_info_path': os.path.join(model_folder, 'model_final_checkpoint.model.pkl')}


def plan_path(network, task, plans_identifier):
    preprocessed_path = os.environ['nnUNet_preprocessed']
    plan_dirpath = os.path.join(preprocessed_path, task)
    plan_path_2d = os.path.join(plan_dirpath, plans_identifier + "_plans_2D.pkl")
    plan_path_3d = os.path.join(plan_dirpath, plans_identifier + "_plans_3D.pkl")

    if network =='2d':
        plan_path = plan_path_2d
    else:
        plan_path = plan_path_3d

    return plan_path

def delete_2d_data(network, task, plans_identifier):
    if network == '2d':
        raise ValueError(f"2D data should not be deleted when performing 2d training.")
    else:
        preprocessed_path = os.environ['nnUNet_preprocessed']
        plan_dirpath = os.path.join(preprocessed_path, task)
        plan_path_2d = os.path.join(plan_dirpath, plans_identifier + "_plans_2D.pkl")

        if os.path.exists(plan_path_2d):
            # load 2d plan to help construct 2D data directory
            with open(plan_path_2d, 'rb') as _file:
                plan_2d = pkl.load(_file)
            data_dir_2d = os.path.join(plan_dirpath, plan_2d['data_identifier'] + '_stage' + str(list(plan_2d['plans_per_stage'].keys())[-1]))
            print(f"\n###########\nDeleting 2D data directory at: {data_dir_2d} \n##############\n")
            shutil.rmtree(data_dir_2d)


def normalize_architecture(reference_plan_path, target_plan_path):
    """
    Take the plan file from reference_plan_path and use its contents to copy architecture into target_plan_path

    NOTE: Here we perform some checks and protection steps so that our assumptions if not correct will more
          likely leed to an exception.
    
    """
    
    assert_same_keys = ['num_stages', 'num_modalities', 'modalities', 'normalization_schemes', 'num_classes', 'all_classes', 'base_num_features', 
                        'use_mask_for_norm', 'keep_only_largest_region', 'min_region_size_per_class', 'min_size_per_class', 'transpose_forward', 
                        'transpose_backward', 'preprocessor_name', 'conv_per_stage', 'data_identifier']
    copy_over_keys = ['plans_per_stage']
    nullify_keys = ['original_spacings', 'original_sizes']
    leave_alone_keys = ['list_of_npz_files', 'preprocessed_data_folder', 'dataset_properties']
 

    # check I got all keys here
    assert set(copy_over_keys).union(set(assert_same_keys)).union(set(nullify_keys)).union(set(leave_alone_keys)) == set(['num_stages', 'num_modalities', 'modalities', 'normalization_schemes', 'dataset_properties', 'list_of_npz_files', 'original_spacings', 'original_sizes', 'preprocessed_data_folder', 'num_classes', 'all_classes', 'base_num_features', 'use_mask_for_norm', 'keep_only_largest_region', 'min_region_size_per_class', 'min_size_per_class', 'transpose_forward', 'transpose_backward', 'data_identifier', 'plans_per_stage', 'preprocessor_name', 'conv_per_stage'])
    
    def get_pickle_obj(path):
        with open(path, 'rb') as _file:
            plan= pkl.load(_file)
        return plan 

    def write_pickled_obj(obj, path):
        with open(path, 'wb') as _file:
            pkl.dump(obj, _file) 

    reference_plan = get_pickle_obj(path=reference_plan_path)
    target_plan = get_pickle_obj(path=target_plan_path)

    for key in assert_same_keys:
        if reference_plan[key] != target_plan[key]:
            raise ValueError(f"normalize architecture failed since the reference and target plans differed in at least key: {key}")
    for key in copy_over_keys:
        target_plan[key] = reference_plan[key]
    for key in nullify_keys:
        target_plan[key] = None
    # leave alone keys are left alone :)

    # write back to target plan
    write_pickled_obj(obj=target_plan, path=target_plan_path) 


def trim_data_and_setup_nnunet_models(tasks, network, network_trainer, plans_identifier, fold, init_model_path, init_model_info_path, cuda_device='0'):

    col_0_task = tasks[0]
    # trim collaborator 0 data if appropriate
    if network != '2d':
        delete_2d_data(network=network, task=col_0_task, plans_identifier=plans_identifier)
    # get the architecture info from the first collaborator 0 data setup results, and create its model folder (writing the initial model info into it)
    col_0_plan_path = plan_path(network=network, task=col_0_task, plans_identifier=plans_identifier)

    col_0_model_folder = model_folder(network=network, 
                                      task=col_0_task, 
                                      network_trainer=network_trainer, 
                                      plans_identifier=plans_identifier, 
                                      fold=fold)
    os.makedirs(col_0_model_folder, exist_ok=False)

    col_0_model_files_dict = model_paths_from_folder(model_folder=model_folder(network=network, 
                                                                               task=col_0_task, 
                                                                               network_trainer=network_trainer, 
                                                                               plans_identifier=plans_identifier, 
                                                                               fold=fold))
    if not init_model_path:
        # train collaborator 0 for a single epoch to get an initial model
        train_on_task(task=col_0_task, network=network, network_trainer=network_trainer, fold=fold, cuda_device=cuda_device)
        # now copy the final model and info from the initial training run into the initial paths
        shutil.copyfile(src=col_0_model_files_dict['final_model_path'],dst=col_0_model_files_dict['initial_model_path'])
        shutil.copyfile(src=col_0_model_files_dict['final_model_info_path'],dst=col_0_model_files_dict['initial_model_info_path'])
    else:
        print(f"\n######### COPYING INITIAL MODEL FILES INTO COLLABORATOR 0 FOLDERS #########\n")
        # Copy initial model and model info into col_0_model_folder
        shutil.copyfile(src=init_model_path,dst=col_0_model_files_dict['initial_model_path'])
        shutil.copyfile(src=init_model_info_path,dst=col_0_model_files_dict['initial_model_info_path'])
        # now copy the initial model also into the final paths
        shutil.copyfile(src=col_0_model_files_dict['initial_model_path'],dst=col_0_model_files_dict['final_model_path'])
        shutil.copyfile(src=col_0_model_files_dict['initial_model_info_path'],dst=col_0_model_files_dict['final_model_info_path'])

    # now create the model folders for collaborators 1 and upward, populate them with the model files from 0, 
    # and replace their data directory plan files from the col_0 plan 
    for col_idx_minus_one, task in enumerate(tasks[1:]):
        # trim collaborator data if appropriate
        if network != '2d':
            delete_2d_data(network=network, task=task, plans_identifier=plans_identifier)

        print(f"\n######### COPYING MODEL INFO FROM COLLABORATOR 0 TO COLLABORATOR {col_idx_minus_one + 1} #########\n")
        # replace data directory plan file with one from col_0
        target_plan_path = plan_path(network=network, task=task, plans_identifier=plans_identifier)
        normalize_architecture(reference_plan_path=col_0_plan_path, target_plan_path=target_plan_path)

        # create model folder for this collaborator
        this_col_model_folder = model_folder(network=network, 
                                             task=task, 
                                             network_trainer=network_trainer, 
                                             plans_identifier=plans_identifier, 
                                             fold=fold)
        os.makedirs(this_col_model_folder, exist_ok=False)

        # copy model, and model info files from col_0 to this collaborator's model folder
        this_col_model_files_dict = model_paths_from_folder(model_folder=model_folder(network=network, 
                                                                                      task=task, 
                                                                                      network_trainer=network_trainer, 
                                                                                      plans_identifier=plans_identifier, 
                                                                                      fold=fold))
        # Copy initial and final model and model info from col_0 into this_col_model_folder
        shutil.copyfile(src=col_0_model_files_dict['initial_model_path'],dst=this_col_model_files_dict['initial_model_path'])
        shutil.copyfile(src=col_0_model_files_dict['final_model_path'],dst=this_col_model_files_dict['final_model_path'])
        shutil.copyfile(src=col_0_model_files_dict['initial_model_info_path'],dst=this_col_model_files_dict['initial_model_info_path'])
        shutil.copyfile(src=col_0_model_files_dict['final_model_info_path'],dst=this_col_model_files_dict['final_model_info_path'])
    