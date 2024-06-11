# Copyright (C) 2020-2021 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Contributors: Brandon Edwards, Micah Sheller

"""
import os
import subprocess
import pickle as pkl
import shutil
import numpy as np

from collections import OrderedDict

from nnunet.dataset_conversion.utils import generate_dataset_json

from nnunet_model_setup import trim_data_and_setup_nnunet_models


num_to_modality = {'_0000': '_brain_t1n.nii.gz',
                   '_0001': '_brain_t2w.nii.gz',
                   '_0002': '_brain_t1c.nii.gz',
                   '_0003': '_brain_t2f.nii.gz'}


def get_subdirs(parent_directory):
    subjects = os.listdir(parent_directory)
    # print("before filter:", subjects)
    subjects = [p for p in subjects if os.path.isdir(os.path.join(parent_directory, p)) and not p.startswith(".")]
    # print("after filter:", subjects)
    return subjects


def subject_time_to_mask_path(pardir, subject, timestamp):
    mask_fname = f'{subject}_{timestamp}_tumorMask_model_0.nii.gz'
    return os.path.join(pardir, 'labels', '.tumor_segmentation_backup', subject, timestamp,'TumorMasksForQC', mask_fname)


def create_task_folders(first_three_digit_task_num, num_institutions, task_name):
    """
    Creates task folders for all simulated instiutions in the federation
    """
    nnunet_dst_pardirs = []
    nnunet_images_train_pardirs = []
    nnunet_labels_train_pardirs = []

    task_nums = range(first_three_digit_task_num, first_three_digit_task_num + num_institutions)
    tasks = [f'Task{str(num)}_{task_name}' for num in task_nums]
    for task in tasks:

        # The NNUnet data path is obtained from an environmental variable
        nnunet_dst_pardir = os.path.join(os.environ['nnUNet_raw_data_base'], 'nnUNet_raw_data', f'{task}')
            
        nnunet_images_train_pardir = os.path.join(nnunet_dst_pardir, 'imagesTr')
        nnunet_labels_train_pardir = os.path.join(nnunet_dst_pardir, 'labelsTr')

        if os.path.exists(nnunet_images_train_pardir) and os.path.exists(nnunet_labels_train_pardir):
            raise ValueError(f"Train images pardirs: {nnunet_images_train_pardir} and {nnunet_labels_train_pardir} both already exist. Please move them both and rerun to prevent overwriting.")
        elif os.path.exists(nnunet_images_train_pardir):
            raise ValueError(f"Train images pardir: {nnunet_images_train_pardir} already exists, please move and run again to prevent overwriting.")
        elif os.path.exists(nnunet_labels_train_pardir):
            raise ValueError(f"Train labels pardir: {nnunet_labels_train_pardir} already exists, please move and run again to prevent overwriting.")
        
        os.makedirs(nnunet_images_train_pardir, exist_ok=False)
        os.makedirs(nnunet_labels_train_pardir, exist_ok=False) 
        
        nnunet_dst_pardirs.append(nnunet_dst_pardir)
        nnunet_images_train_pardirs.append(nnunet_images_train_pardir)
        nnunet_labels_train_pardirs.append(nnunet_labels_train_pardir)

    return task_nums, tasks, nnunet_dst_pardirs, nnunet_images_train_pardirs, nnunet_labels_train_pardirs
    

def symlink_one_subject(postopp_subject_dir, postopp_data_dirpath, postopp_labels_dirpath, nnunet_images_train_pardir, nnunet_labels_train_pardir, timestamp_selection):
    postopp_subject_dirpath = os.path.join(postopp_data_dirpath, postopp_subject_dir)
    all_timestamps = get_subdirs(postopp_subject_dirpath)
    if timestamp_selection == 'latest':
        timestamps = all_timestamps[-1:]
    elif timestamp_selection == 'earliest':
        timestamps = all_timestamps[0:1]
    elif timestamp_selection == 'all':
        timestamps = all_timestamps
    else:
        raise ValueError(f"timestamp_selection currently only supports 'latest', 'earliest', and 'all', but you have requested: '{timestamp_selection}'")
            
    for timestamp in timestamps:
        postopp_subject_timestamp_dirpath = os.path.join(postopp_subject_dirpath, timestamp)
        postopp_subject_timestamp_label_dirpath = os.path.join(postopp_labels_dirpath, postopp_subject_dir, timestamp)
        if not os.path.exists(postopp_subject_timestamp_label_dirpath):
            raise ValueError(f"Subject label file for data at: {postopp_subject_timestamp_dirpath} was not found in the expected location: {postopp_subject_timestamp_label_dirpath}")
        
        timed_subject = postopp_subject_dir + '_' + timestamp

        # Symlink label first
        label_src_path = os.path.join(postopp_subject_timestamp_label_dirpath, timed_subject + '_final_seg.nii.gz')
        label_dst_path = os.path.join(nnunet_labels_train_pardir, timed_subject + '.nii.gz')
        os.symlink(src=label_src_path, dst=label_dst_path)

        # Symlink images
        for num in num_to_modality:
            src_path = os.path.join(postopp_subject_timestamp_dirpath, timed_subject + num_to_modality[num])
            dst_path = os.path.join(nnunet_images_train_pardir,timed_subject + num + '.nii.gz')
            os.symlink(src=src_path, dst=dst_path)

    return timestamps


def doublecheck_postopp_pardir(postopp_pardir, verbose=False):
    if verbose:
        print(f"Checking postopp_pardir: {postopp_pardir}")
    postopp_subdirs = get_subdirs(postopp_pardir)
    if 'data' not in postopp_subdirs:
        raise ValueError(f"'data' must be a subdirectory of postopp_src_pardir:{postopp_pardir}, but it is not.")
    if 'labels' not in postopp_subdirs:
        raise ValueError(f"'labels' must be a subdirectory of postopp_src_pardir:{postopp_pardir}, but it is not.")
    

def split_by_subject(subject_to_timestamps, percent_train, verbose=False):
    """
    NOTE: An attempt is made to put percent_train of the total subjects into train (as opposed to val) regardless of how many timestamps there are for each subject. 
     No subject is allowed to have samples in both train and val.
    """

    subjects = list(subject_to_timestamps.keys())
    np.random.shuffle(subjects)

    train_cutoff = int(len(subjects) * percent_train)

    train_subject_to_timestamps = {subject: subject_to_timestamps[subject] for subject in subjects[:train_cutoff] }
    val_subject_to_timestamps = {subject: subject_to_timestamps[subject] for subject in subjects[train_cutoff:]}

    return train_subject_to_timestamps, val_subject_to_timestamps


def split_by_timed_subjects(subject_to_timestamps, percent_train, random_tries=30, verbose=False):
    """
    NOTE: An attempt is made to put percent_train of the subject timestamp combinations into train (as opposed to val) regardless of what that does to the subject ratios. 
    No subject is allowed to have samples in both train and val.
    """
    def percent_train_for_split(train_subjects, grand_total):
        sub_total = 0
        for subject in train_subjects:
            sub_total += subject_counts[subject]
        return sub_total/grand_total

    def shuffle_and_cut(subject_counts, grand_total, percent_train, verbose=False):
        subjects = list(subject_counts.keys())
        np.random.shuffle(subjects)
        for idx in range(2,len(subjects)+1):
            train_subjects = subjects[:idx-1]
            val_subjects = subjects[idx-1:]
            percent_train_estimate = percent_train_for_split(train_subjects=train_subjects, grand_total=grand_total)
            if percent_train_estimate >= percent_train:
                """
                if verbose:
                    print(f"SPLIT COMPUTE - Found one split with percent_train of: {percent_train_estimate}")
                """
                break
        return train_subjects, val_subjects, percent_train_estimate
        # above should return by end of loop as percent_train_estimate should be strictly increasing with final value 1.0
            
        
    subject_counts = {subject: len(subject_to_timestamps[subject]) for subject in subject_to_timestamps}
    subjects_copy = list(subject_counts.keys()).copy()
    grand_total = 0
    for subject in subject_counts:
        grand_total += subject_counts[subject]

    # create a valid split of counts for comparison
    best_train_subjects = subjects_copy[:1]
    best_val_subjects = subjects_copy[1:]
    best_percent_train = percent_train_for_split(train_subjects=best_train_subjects, grand_total=grand_total)

    # random shuffle <random_tries> times in order to find the closest we can get to honoring the percent_train requirement (train and val both need to be non-empty)
    for _ in range(random_tries):
        train_subjects, val_subjects, percent_train_estimate = shuffle_and_cut(subject_counts=subject_counts, grand_total=grand_total, percent_train=percent_train, verbose=verbose)
        if abs(percent_train_estimate - percent_train) < abs(best_percent_train - percent_train):
            best_train_subjects = train_subjects
            best_val_subjects = val_subjects
            best_percent_train = percent_train_estimate
    if verbose:
        print(f"\n#########\n Split was performed by timed subject and an error of {abs(best_percent_train - percent_train)} was acheived in the percent train target.")
    train_subject_to_timestamps = {subject: subject_to_timestamps[subject] for subject in best_train_subjects}
    val_subject_to_timestamps = {subject: subject_to_timestamps[subject] for subject in best_val_subjects}
    return train_subject_to_timestamps, val_subject_to_timestamps
  

def write_splits_file(nnunet_dst_pardir, subject_to_timestamps, percent_train, split_logic, fold, task, splits_fname='splits_final.pkl', verbose=False):
    # double check we are in the right folder to modify the splits file
    splits_fpath = os.path.join(os.environ['nnUNet_preprocessed'], f'{task}', splits_fname)

    # now split
    if split_logic == 'by_subject':
        train_subject_to_timestamps, val_subject_to_timestamps = split_by_subject(subject_to_timestamps=subject_to_timestamps, percent_train=percent_train, verbose=verbose)
    elif split_logic == 'by_subject_time_pair':
        train_subject_to_timestamps, val_subject_to_timestamps = split_by_timed_subjects(subject_to_timestamps=subject_to_timestamps, percent_train=percent_train, verbose=verbose)    
    else:
        raise ValueError(f"Split logic of 'by_subject' and 'by_subject_time_pair' are the only ones supported, whereas a split_logic value of {split_logic} was provided.")

    # Now construct the list of subjects
    train_subjects_list = []
    val_subjects_list = []
    for subject in train_subject_to_timestamps:
        for timestamp in train_subject_to_timestamps[subject]:
            train_subjects_list.append(subject + '_' + timestamp)
    for subject in val_subject_to_timestamps:
        for timestamp in val_subject_to_timestamps[subject]:
            val_subjects_list.append(subject + '_' + timestamp)

    # Now write the splits file (note None is put into the folds that we don't use as a safety measure so that no unintended folds are used)
    new_folds = [None, None, None, None, None]
    new_folds[int(fold)] = OrderedDict({'train': np.array(train_subjects_list), 'val': np.array(val_subjects_list)})
    with open(splits_fpath, 'wb') as f:
        pkl.dump(new_folds, f)


def setup_nnunet_data(postopp_pardirs, 
                      first_three_digit_task_num, 
                      task_name, 
                      percent_train, 
                      split_logic, 
                      fold, 
                      timestamp_selection, 
                      num_institutions, 
                      network, 
                      network_trainer, 
                      plans_identifier, 
                      init_model_path, 
                      init_model_info_path, 
                      cuda_device, 
                      verbose=False):
    """
    Generates symlinks to be used for NNUnet training, assuming we already have a 
    dataset on file coming from MLCommons RANO experiment data prep.

    Also creates the json file for the data, as well as runs nnunet preprocessing.

    should be run using a virtual environment that has nnunet version 1 installed.

    args:
    postopp_pardirs(list of str)     : Parent directories for postopp data. The length of the list should either be 
                                   equal to num_insitutions, or one. If the length of the list is one and num_insitutions is not one,
                                   the samples within that single directory will be used to create num_insititutions shards.
                                   If the length of this list is equal to num_insitutions, the shards are defined by the samples within each string path.  
                                   Either way, all string paths within this list should piont to folders that have 'data' and 'labels' subdirectories with structure:
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

    first_three_digit_task_num(str): Should start with '5'. If num_institutions == N (see below), all N task numbers starting with this number will be used.
    task_name(str)                 : Any string task name.
    timestamp_selection(str)       : Indicates how to determine the timestamp to pick
                                   for each subject ID at the source: 'latest', 'earliest', and 'all' are the only ones supported so far
    percent_train(float)            : What percentage of timestamped subjects to attempt dedicate to train versus val. Will be only approximately acheived in general since
                                      all timestamps associated with the same subject need to land exclusively in either train or val.
    split_logic(str)                : Determines how the percent_train is computed. Choices are: 'by_subject' and 'by_subject_time_pair'.
    fold(str)                       :   Fold to train on, can be a sting indicating an int, or can be 'all'
    num_institutions(int)          : Number of simulated institutions to shard the data into.
    verbose(bool)                   : Debugging output if True.

    Returns:
    task_nums, tasks, nnunet_dst_pardirs, nnunet_images_train_pardirs, nnunet_labels_train_pardirs 
    """

    task_nums, tasks, nnunet_dst_pardirs, nnunet_images_train_pardirs, nnunet_labels_train_pardirs = \
        create_task_folders(first_three_digit_task_num=first_three_digit_task_num, 
                            num_institutions=num_institutions, 
                            task_name=task_name)

    if len(postopp_pardirs) == 1:
        postopp_pardir = postopp_pardirs[0]
        doublecheck_postopp_pardir(postopp_pardir, verbose=verbose)
        postopp_data_dirpaths = num_institutions * [os.path.join(postopp_pardir, 'data')]
        postopp_labels_dirpaths = num_institutions * [os.path.join(postopp_pardir, 'labels')]

        all_subjects = get_subdirs(postopp_data_dirpaths[0])
        subject_shards = [all_subjects[start::num_institutions] for start in range(num_institutions)]
    elif len(postopp_pardirs) != num_institutions:
        raise ValueError(f"The length of postopp_pardirs must be equal to the number of insitutions needed for the federation, or can be length one and an automated split is peroformed.")
    else:
        subject_shards = []
        postopp_data_dirpaths = []
        postopp_labels_dirpaths = []
        for postopp_pardir in postopp_pardirs:
            doublecheck_postopp_pardir(postopp_pardir, verbose=verbose)
            postopp_data_dirpath = os.path.join(postopp_pardir, 'data')
            postopp_labels_dirpath = os.path.join(postopp_pardir, 'labels')
            postopp_data_dirpaths.append(postopp_data_dirpath)
            postopp_labels_dirpaths.append(postopp_labels_dirpath)
            subject_shards.append(get_subdirs(postopp_labels_dirpath))
    
    # Track the subjects and timestamps for each shard
    shard_subject_to_timestamps = []

    for shard_idx, (postopp_subject_dirs, task_num, task, nnunet_dst_pardir, nnunet_images_train_pardir, nnunet_labels_train_pardir, postopp_data_dirpath, postopp_labels_dirpath) in \
          enumerate(zip(subject_shards, task_nums, tasks, nnunet_dst_pardirs, nnunet_images_train_pardirs, nnunet_labels_train_pardirs, postopp_data_dirpaths, postopp_labels_dirpaths)):
        print(f"\n######### CREATING SYMLINKS TO POSTOPP DATA FOR COLLABORATOR {shard_idx} #########\n")
        subject_to_timestamps = {} 
        for postopp_subject_dir in postopp_subject_dirs:
            subject_to_timestamps[postopp_subject_dir] = symlink_one_subject(postopp_subject_dir=postopp_subject_dir, 
                                                                               postopp_data_dirpath=postopp_data_dirpath, 
                                                                               postopp_labels_dirpath=postopp_labels_dirpath, 
                                                                               nnunet_images_train_pardir=nnunet_images_train_pardir, 
                                                                               nnunet_labels_train_pardir=nnunet_labels_train_pardir, 
                                                                               timestamp_selection=timestamp_selection)
        shard_subject_to_timestamps.append(subject_to_timestamps)
        
        # Generate json file for the dataset
        print(f"\n######### GENERATING DATA JSON FILE FOR COLLABORATOR {shard_idx} #########\n")
        json_path = os.path.join(nnunet_dst_pardir, 'dataset.json')
        labels = {0: 'Background', 1: 'Necrosis', 2: 'Edema', 3: 'Enhancing Tumor', 4: 'Cavity'}
        # labels = {0: 'Background', 1: 'Necrosis', 2: 'Edema'}
        # print(f"{nnunet_images_train_pardir}")
        # print(list(os.listdir(nnunet_images_train_pardir)))

        
        # from typing import List, Union
        # def subfiles(folder: str, join: bool = True, prefix: Union[List[str], str] = None,
        #     suffix: Union[List[str], str] = None, sort: bool = True) -> List[str]:
        #     if join:
        #         l = os.path.join
        #     else:
        #         l = lambda x, y: y

        #     if prefix is not None and isinstance(prefix, str):
        #         prefix = [prefix]
        #     if suffix is not None and isinstance(suffix, str):
        #         suffix = [suffix]
        #     print([ i for i in os.listdir(folder)])
        #     print([ i for i in os.listdir(folder) if os.path.isfile(os.path.join(folder, i)) ])
        #     res = [l(folder, i) for i in os.listdir(folder) if os.path.isfile(os.path.join(folder, i))
        #         and (prefix is None or any([i.startswith(j) for j in prefix]))
        #         and (suffix is None or any([i.endswith(j) for j in suffix]))]

        #     if sort:
        #         res.sort()
        #     return res
        

        # uniques = np.unique([i[:-12] for i in subfiles(nnunet_images_train_pardir, suffix='.nii.gz', join=False)])
        # print("UNIQUES::::\n",uniques)
        generate_dataset_json(output_file=json_path, 
                              imagesTr_dir=nnunet_images_train_pardir, 
                              imagesTs_dir=None, 
                              modalities=tuple(num_to_modality.keys()),
                              labels=labels, 
                              dataset_name='RANO Postopp')
        
        # Now call the os process to preprocess the data
        print(f"\n######### OS CALL TO PREPROCESS DATA FOR COLLABORATOR {shard_idx} #########\n")
        subprocess.run(["nnUNet_plan_and_preprocess",  "-t",  f"{task_num}", "--verify_dataset_integrity"])

    # trim 2d data if not working with 2d model, and distribute common model architecture across simulated collaborators
    trim_data_and_setup_nnunet_models(tasks=tasks, 
                                      network=network, 
                                      network_trainer=network_trainer, 
                                      plans_identifier=plans_identifier, 
                                      fold=fold, 
                                      init_model_path=init_model_path, 
                                      init_model_info_path=init_model_info_path, 
                                      cuda_device=cuda_device)
    
    
    for task, subject_to_timestamps in zip(tasks, shard_subject_to_timestamps):
        # Now compute our own stratified splits file, keeping all timestampts for a given subject exclusively in either train or val
        write_splits_file(nnunet_dst_pardir=nnunet_dst_pardir, 
                          subject_to_timestamps=subject_to_timestamps, 
                          percent_train=percent_train, 
                          split_logic=split_logic, 
                          fold=fold, 
                          task=task, 
                          verbose=verbose)
    
