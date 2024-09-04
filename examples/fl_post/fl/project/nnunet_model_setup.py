import os
import pickle as pkl
import shutil

from src.nnunet_v1 import train_nnunet
from nnunet.paths import default_plans_identifier

def train_on_task(task, network, network_trainer, fold, cuda_device, plans_identifier, continue_training=False, current_epoch=0):
    os.environ['CUDA_VISIBLE_DEVICES']=cuda_device
    print(f"###########\nStarting training for task: {task}\n")
    train_nnunet(epochs=1, 
                 current_epoch = current_epoch, 
                 network = network,
                 task=task, 
                 network_trainer = network_trainer, 
                 fold=fold, 
                 continue_training=continue_training, 
                 p=plans_identifier)


def get_model_folder(network, task, network_trainer, plans_identifier, fold, results_folder=os.environ['RESULTS_FOLDER']):
    return os.path.join(results_folder, 'nnUNet',network, task, network_trainer + '__' + plans_identifier, f'fold_{fold}')


def get_col_model_paths(model_folder):
    return {'initial_model_path': os.path.join(model_folder, 'model_initial_checkpoint.model'), 
            'final_model_path': os.path.join(model_folder, 'model_final_checkpoint.model'),
            'initial_model_info_path': os.path.join(model_folder, 'model_initial_checkpoint.model.pkl'), 
            'final_model_info_path': os.path.join(model_folder, 'model_final_checkpoint.model.pkl')}


def get_col_plans_path(network, task, plans_identifier):
    # returning a dictionary in ordre to incorporate it more easily into another paths dict
    preprocessed_path = os.environ['nnUNet_preprocessed']
    plans_write_dirpath = os.path.join(preprocessed_path, task)
    plans_write_path_2d = os.path.join(plans_write_dirpath, plans_identifier + "_plans_2D.pkl")
    plans_write_path_3d = os.path.join(plans_write_dirpath, plans_identifier + "_plans_3D.pkl")

    if network =='2d':
        plans_write_path = plans_write_path_2d
    else:
        plans_write_path = plans_write_path_3d

    return {'plans_path': plans_write_path}

def delete_2d_data(network, task, plans_identifier):
    if network == '2d':
        raise ValueError(f"2D data should not be deleted when performing 2d training.")
    else:
        preprocessed_path = os.environ['nnUNet_preprocessed']
        plan_dirpath = os.path.join(preprocessed_path, task)
        plan_path_2d = os.path.join(plan_dirpath, "nnUNetPlansv2.1_plans_2D.pkl")

        if os.path.exists(plan_dirpath):
            # load 2d plan to help construct 2D data directory
            with open(plan_path_2d, 'rb') as _file:
                plan_2d = pkl.load(_file)
            data_dir_2d = os.path.join(plan_dirpath, plan_2d['data_identifier'] + '_stage' + str(list(plan_2d['plans_per_stage'].keys())[-1]))
            if os.path.exists(data_dir_2d):
                print(f"\n###########\nDeleting 2D data directory at: {data_dir_2d} \n##############\n")
                shutil.rmtree(data_dir_2d)



def trim_data_and_setup_model(task, network, network_trainer, plans_identifier, fold, init_model_path, init_model_info_path, plans_path, cuda_device='0'):
    """
    Note that plans_identifier here is designated from fl_setup.py and is an alternative to the default one due to overwriting of the local plans by a globally distributed one
    """

    # Removing 2D data is not longer needed since we set "-pl2d None during plan and preprocessing call"
    # TODO: remove this comment once tested
    """
    if network != '2d':
        delete_2d_data(network=network, task=task, plans_identifier=plans_identifier)
    """
    
    # get or create architecture info

    model_folder = get_model_folder(network=network, 
                                      task=task, 
                                      network_trainer=network_trainer, 
                                      plans_identifier=plans_identifier, 
                                      fold=fold)
    if not os.path.exists(model_folder):
        os.makedirs(model_folder, exist_ok=False)
    
    col_paths = get_col_model_paths(model_folder=get_model_folder(network=network, 
                                                                             task=task, 
                                                                             network_trainer=network_trainer, 
                                                                             plans_identifier=plans_identifier, 
                                                                             fold=fold))
    col_paths.update(get_col_plans_path(network=network, task=task, plans_identifier=plans_identifier))

    if not init_model_path:
        if plans_path:
            raise ValueError(f"If the initial model is not provided then we do not expect the plans_path to be provided either (plans file and initial model are sourced the same way).")
        # train for a single epoch to get an initial model (this uses the default plans identifier)
        train_on_task(task=task, network=network, network_trainer=network_trainer, fold=fold, cuda_device=cuda_device, plans_identifier=default_plans_identifier)
        # now copy the trained final model and info into the initial paths
        shutil.copyfile(src=col_paths['final_model_path'],dst=col_paths['initial_model_path'])
        shutil.copyfile(src=col_paths['final_model_info_path'],dst=col_paths['initial_model_info_path'])
    else:
        print(f"\n######### WRITING MODEL, MODEL INFO, and PLANS #########\ncol_paths were: {col_paths}\n\n")
        shutil.copy(src=plans_path,dst=col_paths['plans_path'])
        shutil.copyfile(src=init_model_path,dst=col_paths['initial_model_path'])
        shutil.copyfile(src=init_model_info_path,dst=col_paths['initial_model_info_path'])
        # now copy these files also into the final paths
        shutil.copyfile(src=col_paths['initial_model_path'],dst=col_paths['final_model_path'])
        shutil.copyfile(src=col_paths['initial_model_info_path'],dst=col_paths['final_model_info_path'])

    return col_paths['initial_model_path'], col_paths['final_model_path'], col_paths['initial_model_info_path'], col_paths['final_model_info_path'], col_paths['plans_path']