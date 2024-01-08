import os

DSET_HELP = "The Dataset to monitor. If and ID is passed, medperf will be used to identify the dataset. If a path is passed, it will look at that path instead"
MLCUBE_HELP = "The Data Preparation MLCube UID used to create the data"
STAGES_HELP = "Path to stages YAML file containing documentation about the Data Preparation stages"
DEFAULT_SEGMENTATION = "tumorMask_model_0.nii.gz"
DEFAULT_STAGES_PATH = os.path.join(os.path.dirname(__file__), "assets/stages.yaml")
BRAINMASK = "brainMask_fused.nii.gz"
REVIEW_FILENAME = "review_cases.tar.gz"
REVIEW_COMMAND = "itksnap"
MANUAL_REVIEW_STAGE = 5
DONE_STAGE = 8
LISTITEM_MAX_LEN = 30