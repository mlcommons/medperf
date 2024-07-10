import argparse

# We will be syncing training across many nodes who independently preprocess data
# In order to do this we will need to sync the training plans (defining the model architecture etc.)
# NNUnet does this by overwriting the plans file which includes a unique alternative plans identifier other than the default one

from nnunet.paths import default_plans_identifier

from fl_data_setup import setup_fl_data

local_plans_identifier = default_plans_identifier
shared_plans_identifier = 'nnUNetPlans_pretrained_POSTOPP'


def list_of_strings(arg):
    return arg.split(',')

def main(postopp_pardir, 
         three_digit_task_num,  
         task_name, 
         percent_train=0.8, 
         split_logic='by_subject_time_pair', 
         network='3d_fullres', 
         network_trainer='nnUNetTrainerV2', 
         fold='0',
         init_model_path=None, 
         init_model_info_path=None,
         plans_path=None, 
         local_plans_identifier=local_plans_identifier,
         shared_plans_identifier=shared_plans_identifier,
         overwrite_nnunet_datadirs=False, 
         timestamp_selection='all', 
         cuda_device='0', 
         verbose=False):
    """
    Generates symlinks to be used for NNUnet training, assuming we already have a 
    dataset on file coming from MLCommons RANO experiment data prep.

    Also creates the json file for the data, as well as runs nnunet preprocessing.

    should be run using a virtual environment that has nnunet version 1 installed.

    args:
    postopp_pardir(str)     : Parent directory for postopp data, which should contain 'data' and 'labels' subdirectories with structure:
                                    ├── data
                                    │   ├── AAAC_0
                                    │   │   ├── 2008.03.30
                                    │   │   │   ├── AAAC_0_2008.03.30_brain_t1c.nii.gz
                                    │   │   │   ├── AAAC_0_2008.03.30_brain_t1n.nii.gz
                                    │   │   │   ├── AAAC_0_2008.03.30_brain_t2f.nii.gz
                                    │   │   │   └── AAAC_0_2008.03.30_brain_t2w.nii.gz
                                    │   │   └── 2008.12.17
                                    │   │       ├── AAAC_0_2008.12.17_brain_t1c.nii.gz
                                    │   │       ├── AAAC_0_2008.12.17_brain_t1n.nii.gz
                                    │   │       ├── AAAC_0_2008.12.17_brain_t2f.nii.gz
                                    │   │       └── AAAC_0_2008.12.17_brain_t2w.nii.gz
                                    │   ├── AAAC_1
                                    │   │   ├── 2008.03.30_duplicate
                                    │   │   │   ├── AAAC_1_2008.03.30_duplicate_brain_t1c.nii.gz
                                    │   │   │   ├── AAAC_1_2008.03.30_duplicate_brain_t1n.nii.gz
                                    │   │   │   ├── AAAC_1_2008.03.30_duplicate_brain_t2f.nii.gz
                                    │   │   │   └── AAAC_1_2008.03.30_duplicate_brain_t2w.nii.gz
                                    │   │   └── 2008.12.17_duplicate
                                    │   │       ├── AAAC_1_2008.12.17_duplicate_brain_t1c.nii.gz
                                    │   │       ├── AAAC_1_2008.12.17_duplicate_brain_t1n.nii.gz
                                    │   │       ├── AAAC_1_2008.12.17_duplicate_brain_t2f.nii.gz
                                    │   │       └── AAAC_1_2008.12.17_duplicate_brain_t2w.nii.gz
                                    │   ├── AAAC_extra
                                    │   │   └── 2008.12.10
                                    │   │       ├── AAAC_extra_2008.12.10_brain_t1c.nii.gz
                                    │   │       ├── AAAC_extra_2008.12.10_brain_t1n.nii.gz
                                    │   │       ├── AAAC_extra_2008.12.10_brain_t2f.nii.gz
                                    │   │       └── AAAC_extra_2008.12.10_brain_t2w.nii.gz
                                    │   ├── data.csv
                                    │   └── splits.csv
                                    ├── labels
                                    │   ├── AAAC_0
                                    │   │   ├── 2008.03.30
                                    │   │   │   └── AAAC_0_2008.03.30_final_seg.nii.gz
                                    │   │   └── 2008.12.17
                                    │   │       └── AAAC_0_2008.12.17_final_seg.nii.gz
                                    │   ├── AAAC_1
                                    │   │   ├── 2008.03.30_duplicate
                                    │   │   │   └── AAAC_1_2008.03.30_duplicate_final_seg.nii.gz
                                    │   │   └── 2008.12.17_duplicate
                                    │   │       └── AAAC_1_2008.12.17_duplicate_final_seg.nii.gz
                                    │   └── AAAC_extra
                                    │       └── 2008.12.10
                                    │           └── AAAC_extra_2008.12.10_final_seg.nii.gz
                                    └── report.yaml

    three_digit_task_num(str)       : Should start with '5' and not collide with other NNUnet task nums on your system.
    init_model_path (str)           : path to initial (pretrained) model file [default None] - must be provided if init_model_info_path is.
                                      [ONLY USE IF YOU KNOW THE MODEL ARCHITECTURE MAKES SENSE FOR THE FEDERATION.]
    init_model_info_path(str)       : path to initial (pretrained) model info pikle file [default None]- must be provided if init_model_path is.
                                      [ONLY USE IF YOU KNOW THE MODEL ARCHITECTURE MAKES SENSE FOR THE FEDERATION.]
    plans_path(str)                  : Path the the NNUnet plan file
                                      [ONLY USE IF YOU KNOW THE MODEL ARCHITECTURE MAKES SENSE FOR THE FEDERATION.]
    task_name(str)                  : Name of task that is part of the task name
    percent_train(float)            : The percentage of samples to split into the train portion for the fold specified below (NNUnet makes its own folds but we overwrite
                                      all with None except the fold indicated below and put in our own split instead determined by a hard coded split logic default)
    split_logic(str)                : Determines how the percent_train is computed. Choices are: 'by_subject' and 'by_subject_time_pair' (see inner function docstring)
    network(str)                    : NNUnet network to be used
    network_trainer(str)            : NNUnet network trainer to be used
    fold(str)                       : Fold to train on, can be a sting indicating an int, or can be 'all'
    local_plans_identifier(str)     : Used in the plans file naming for collaborators that will be performing local training to produce a pretrained model.
    shared_plans_identifier(str)    : Used in the plans file naming for the shared plan distributed across the federation.
    overwrite_nnunet_datadirs(str)  : Allows overwriting NNUnet directories with task numbers from first_three_digit_task_num to that plus one les than number of insitutions.
    task_name(str)                  : Any string task name.
    timestamp_selection(str)        : Indicates how to determine the timestamp to pick. Only 'earliest', 'latest', or 'all' are supported.
                                      for each subject ID at the source: 'latest' and 'earliest' are the only ones supported so far
    verbose(bool)                   : If True, print debugging information.
    """
    
    # some argument inspection
    if str(three_digit_task_num)[0] != '5':
         raise ValueError(f"The three digit task number: {three_digit_task_num} should start with 5 to avoid NNUnet repository tasks, but it starts with {three_digit_task_num[0]}")    
    if init_model_path or init_model_info_path:
          if not init_model_path or not init_model_info_path:
                raise ValueError(f"If either init_model_path or init_model_info_path are provided, they both must be.")
    if init_model_path:
          if not init_model_path.endswith('.model'):
                raise ValueError(f"Initial model file should end with, '.model'")
          if not init_model_info_path.endswith('.model.pkl'):
                raise ValueError(f"Initial model info file should end with, 'model.pkl'")
          
    # task_folder_info is a zipped lists indexed over tasks (collaborators)
    #                  zip(task_nums, tasks, nnunet_dst_pardirs, nnunet_images_train_pardirs, nnunet_labels_train_pardirs)
    col_paths = setup_fl_data(postopp_pardir=postopp_pardir, 
                             three_digit_task_num=three_digit_task_num, 
                             task_name=task_name,
                             percent_train=percent_train,
                             split_logic=split_logic,
                             fold=fold, 
                             timestamp_selection=timestamp_selection, 
                             network=network, 
                             network_trainer=network_trainer, 
                             local_plans_identifier=local_plans_identifier,
                             shared_plans_identifier=shared_plans_identifier, 
                             init_model_path=init_model_path, 
                             init_model_info_path=init_model_info_path,
                             plans_path=plans_path, 
                             cuda_device=cuda_device,
                             overwrite_nnunet_datadirs=overwrite_nnunet_datadirs,
                             verbose=verbose)
    
    return col_paths

if __name__ == '__main__':

        argparser = argparse.ArgumentParser()
        argparser.add_argument(
            '--postopp_pardir',
            type=str,
            help="Parent directory to postopp data.")
        argparser.add_argument(
            '--three_digit_task_num',
            type=int,
            help="Should start with '5'. If fedsim == N, all N task numbers starting with this number will be used.")
        argparser.add_argument(
            '--init_model_path',
            type=str,
            default=None,
            help="Path to initial (pretrained) model file [ONLY USE IF YOU KNOW THE MODEL ARCHITECTURE MAKES SENSE FOR THE FEDERATION.].")
        argparser.add_argument(
            '--init_model_info_path',
            type=str,
            default=None,
            help="Path to initial (pretrained) model info file [ONLY USE IF YOU KNOW THE MODEL ARCHITECTURE MAKES SENSE FOR THE FEDERATION.].")
        argparser.add_argument(
            '--plans_path',
            type=str,
            default=None,
            help="Path to the training plan file[ONLY USE IF YOU KNOW THE MODEL ARCHITECTURE MAKES SENSE FOR THE FEDERATION.].")
        argparser.add_argument(
            '--task_name',
            type=str,
            help="Part of the NNUnet data task directory name. With 'first_three_digit_task_num being 'XXX', the directory name becomes: .../nnUNet_raw_data_base/nnUNet_raw_data/TaskXXX_<task_name>.")
        argparser.add_argument(
            '--percent_train',
            type=float,
            default=0.8,
            help="The percentage of samples to split into the train portion for the fold specified below (NNUnet makes its own folds but we overwrite) - see docstring in main")
        argparser.add_argument(
          '--split_logic',
            type=str,
            default='by_subject_time_pair',
            help="Determines how the percent_train is computed. Choices are: 'by_subject' and 'by_subject_time_pair' (see inner function docstring)")
        argparser.add_argument(
          '--network',
            type=str,
            default='3d_fullres',
            help="NNUnet network to be used.")
        argparser.add_argument(
            '--network_trainer',
            type=str,
            default='nnUNetTrainerV2',
            help="NNUnet network trainer to be used.")
        argparser.add_argument(
            '--fold',
            type=str,
            default='0',
            help="Fold to train on, can be a sting indicating an int, or can be 'all'.")
        argparser.add_argument(
            '--timestamp_selection',
            type=str,
            default='all',
            help="Indicates how to determine the timestamp to pick for each subject ID at the source: 'latest' and 'earliest' are the only ones supported so far.")        
        argparser.add_argument(
            '--cuda_device',
            type=str,
            default='0',
            help="Used for the setting of os.environ['CUDA_VISIBLE_DEVICES']")
        argparser.add_argument(
            '--overwrite_nnunet_datadirs',
            action='store_true',
            help="Allows overwriting NNUnet directories with task numbers from first_three_digit_task_num to that plus one les than number of insitutions.")
        argparser.add_argument(
            '--verbose',
            action='store_true',
            help="Print debuging information.")    

        args = argparser.parse_args()

        kwargs = vars(args)

        main(**kwargs)
