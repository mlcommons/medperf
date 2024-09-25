



# The following was copied and modified from the source: 
# https://github.com/kaapana/kaapana/blob/26d71920d53c3110e2494cbb2ddb0cbb996b880a/data-processing/base-images/base-nnunet/files/patched/run_training.py#L213


#    Copyright 2020 Division of Medical Image Computing, German Cancer Research Center (DKFZ), Heidelberg, Germany
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.


import os
import numpy as np
import torch
import random
from batchgenerators.utilities.file_and_folder_operations import *
from nnunet.run.default_configuration import get_default_configuration
from nnunet.run.load_pretrained_weights import load_pretrained_weights
from nnunet.training.cascade_stuff.predict_next_stage import predict_next_stage
from nnunet.training.network_training.nnUNetTrainer import nnUNetTrainer
from nnunet.training.network_training.nnUNetTrainerCascadeFullRes import (
    nnUNetTrainerCascadeFullRes,
)
from nnunet.training.network_training.nnUNetTrainerV2_CascadeFullRes import (
    nnUNetTrainerV2CascadeFullRes,
)
from nnunet.utilities.task_name_id_conversion import convert_id_to_task_name


# We will be syncing training across many nodes who independently preprocess data
# In order to do this we will need to sync the training plans (defining the model architecture etc.)
# NNUnet does this by overwriting the plans file which includes a unique alternative plans identifier other than the default one
plans_param = 'nnUNetPlans_pretrained_POSTOPP'
#from nnunet.paths import default_plans_identifier

def seed_everything(seed=1234):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.backends.cudnn.deterministic = True


def train_nnunet(TOTAL_max_num_epochs, 
                 epochs,
                 current_epoch,
                 train_cutoff=np.inf,
                 val_cutoff=np.inf,
                 network='3d_fullres', 
                 network_trainer='nnUNetTrainerV2', 
                 task='Task543_FakePostOpp_More', 
                 fold='0', 
                 continue_training=True,
                 validation_only=False, 
                 c=False, 
                 p=plans_param, 
                 use_compressed_data=False, 
                 deterministic=False, 
                 npz=False, 
                 find_lr=False, 
                 valbest=False, 
                 fp32=False, 
                 val_folder='validation_raw', 
                 disable_saving=False, 
                 disable_postprocessing_on_folds=True, 
                 val_disable_overwrite=True, 
                 disable_next_stage_pred=False, 
                 pretrained_weights=None):

    """
    TOTAL_max_num_epochs (int): Provides the total number of epochs intended to be trained (this needs to be held constant outside of individual calls to this function during the course of federated training)
    epochs (int): Number of epochs to trainon top of current epoch
    current_epoch (int): Which epoch will be used to grab the model
    train_val_cutoff (int): Total time (in seconds) limit to use in approximating a restriction to training and validation activities.
    train_cutoff_part (float): Portion of train_val_cutoff going to training
    val_cutoff_part (float): Portion of train_val_cutoff going to val
    task (int): can be task name or task id
    fold: "0, 1, ..., 5 or 'all'"
    validation_only: use this if you want to only run the validation
    c: use this if you want to continue a training
    p: plans identifier. Only change this if you created a custom experiment planner
    use_compressed_data: "If you set use_compressed_data, the training cases will not be decompressed. Reading compressed data "
        "is much more CPU and RAM intensive and should only be used if you know what you are "
        "doing"
    deterministic: "Makes training deterministic, but reduces training speed substantially. I (Fabian) think "
        "this is not necessary. Deterministic training will make you overfit to some random seed. "
        "Don't use that."
    npz: "if set then nnUNet will "
        "export npz files of "
        "predicted segmentations "
        "in the validation as well. "
        "This is needed to run the "
        "ensembling step so unless "
        "you are developing nnUNet "
        "you should enable this"
    find_lr: not used here, just for fun
    valbest: hands off. This is not intended to be used
    fp32: disable mixed precision training and run old school fp32
    val_folder: name of the validation folder. No need to use this for most people
    disable_saving: If set nnU-Net will not save any parameter files (except a temporary checkpoint that "
        "will be removed at the end of the training). Useful for development when you are "
        "only interested in the results and want to save some disk space
    disable_postprocessing_on_folds: Running postprocessing on each fold only makes sense when developing with nnU-Net and "
        "closely observing the model performance on specific configurations. You do not need it "
        "when applying nnU-Net because the postprocessing for this will be determined only once "
        "all five folds have been trained and nnUNet_find_best_configuration is called. Usually "
        "running postprocessing on each fold is computationally cheap, but some users have "
        "reported issues with very large images. If your images are large (>600x600x600 voxels) "
        "you should consider setting this flag.
    val_disable_overwrite: If True, validation does not overwrite existing segmentations
    pretrained_wieghts: path to nnU-Net checkpoint file to be used as pretrained model (use .model "
        "file, for example model_final_checkpoint.model). Will only be used when actually training. "
        "Optional. Beta. Use with caution."
    disable_next_stage_pred: If True, do not predict next stage
    """  

    class Arguments():
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    args = Arguments(**locals())

    if args.deterministic:
        seed_everything()

    task = args.task
    fold = args.fold
    network = args.network
    network_trainer = args.network_trainer
    validation_only = args.validation_only
    plans_identifier = args.p
    find_lr = args.find_lr
    disable_postprocessing_on_folds = args.disable_postprocessing_on_folds

    use_compressed_data = args.use_compressed_data
    decompress_data = not use_compressed_data

    deterministic = args.deterministic
    valbest = args.valbest

    fp32 = args.fp32
    run_mixed_precision = not fp32

    val_folder = args.val_folder
    # interp_order = args.interp_order
    # interp_order_z = args.interp_order_z
    # force_separate_z = args.force_separate_z

    if not task.startswith("Task"):
        task_id = int(task)
        task = convert_id_to_task_name(task_id)

    if fold == "all":
        pass
    else:
        fold = int(fold)

    # if force_separate_z == "None":
    #     force_separate_z = None
    # elif force_separate_z == "False":
    #     force_separate_z = False
    # elif force_separate_z == "True":
    #     force_separate_z = True
    # else:
    #     raise ValueError("force_separate_z must be None, True or False. Given: %s" % force_separate_z)
    (
        plans_file,
        output_folder_name,
        dataset_directory,
        batch_dice,
        stage,
        trainer_class,
    ) = get_default_configuration(network, task, network_trainer, plans_identifier)

    if trainer_class is None:
        raise RuntimeError(
            "Could not find trainer class in nnunet.training.network_training"
        )

    if network == "3d_cascade_fullres":
        assert issubclass(
            trainer_class, (nnUNetTrainerCascadeFullRes, nnUNetTrainerV2CascadeFullRes)
        ), (
            "If running 3d_cascade_fullres then your "
            "trainer class must be derived from "
            "nnUNetTrainerCascadeFullRes"
        )
    else:
        assert issubclass(
            trainer_class, nnUNetTrainer
        ), "network_trainer was found but is not derived from nnUNetTrainer"

    trainer = trainer_class(
        plans_file,
        fold,
        TOTAL_max_num_epochs=TOTAL_max_num_epochs,
        output_folder=output_folder_name,
        dataset_directory=dataset_directory,
        batch_dice=batch_dice,
        stage=stage,
        unpack_data=decompress_data,
        deterministic=deterministic,
        fp16=run_mixed_precision,
    )
    # we want latest checkoint only (not best or any intermediate) 
    trainer.save_final_checkpoint = (
        True  # whether or not to save the final checkpoint
    )
    trainer.save_best_checkpoint = (
        False  # whether or not to save the best checkpoint according to
    )
    # self.best_val_eval_criterion_MA
    trainer.save_intermediate_checkpoints = (
        False  # whether or not to save checkpoint_latest. We need that in case
    )
    # the training chashes
    trainer.save_latest_only = (
        True  # if false it will not store/overwrite _latest but separate files each
    )
    trainer.max_num_epochs = current_epoch + epochs
    trainer.epoch = current_epoch

    # TODO: call validation separately
    trainer.initialize(not validation_only)

    # infer total data size and batch size in order to get how many batches to apply so that over many epochs, each data
    # point is expected to be seen epochs number of times

    num_train_batches_per_epoch = int(np.ceil(len(trainer.dataset_tr)/trainer.batch_size))
    num_val_batches_per_epoch = int(np.ceil(len(trainer.dataset_val)/trainer.batch_size))

    # the nnunet trainer attributes have a different naming convention than I am using
    trainer.num_batches_per_epoch = num_train_batches_per_epoch
    trainer.num_val_batches_per_epoch = num_val_batches_per_epoch

    if os.getenv("PREP_INCREMENT_STEP", None) == "from_dataset_properties":
        trainer.save_checkpoint(
            join(trainer.output_folder, "model_final_checkpoint.model")
        )
        print("Preparation round: Model-averaging")
        return

    if find_lr:
        trainer.find_lr()
    else:
        if not validation_only:
            if args.continue_training:
                # -c was set, continue a previous training and ignore pretrained weights
                trainer.load_latest_checkpoint()
            elif (not args.continue_training) and (args.pretrained_weights is not None):
                # we start a new training. If pretrained_weights are set, use them
                load_pretrained_weights(trainer.network, args.pretrained_weights)
            else:
                # new training without pretraine weights, do nothing
                pass

            batches_applied_train, batches_applied_val = trainer.run_training(train_cutoff=train_cutoff, val_cutoff=val_cutoff)
        else:
            # if valbest:
            #     trainer.load_best_checkpoint(train=False)
            # else:
            #     trainer.load_final_checkpoint(train=False)
            trainer.load_latest_checkpoint()

        train_completed = batches_applied_train / float(num_train_batches_per_epoch)
        val_completed = batches_applied_val / float(num_val_batches_per_epoch)
        
        return train_completed, val_completed

        
