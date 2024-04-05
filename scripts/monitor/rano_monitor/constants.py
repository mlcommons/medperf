import os

filepath = os.path.dirname(__file__)

DSET_HELP = (
    "The Dataset to monitor. If and ID is passed, "
    + "medperf will be used to identify the dataset. "
    + "If a path is passed, it will look at that path instead"
)
DSET_LOC_HELP = (
    "Location of the dataset. "
    + "If not provided defaults to Medperf storage search"
)
MLCUBE_HELP = "The Data Preparation MLCube UID used to create the data"
STAGES_HELP = (
    "Path to stages YAML file containing "
    + "documentation about the Data Preparation stages"
)
OUT_HELP = "CSV file to store report in"
DEFAULT_SEGMENTATION = "tumorMask_model_0.nii.gz"
DEFAULT_STAGES_PATH = os.path.join(filepath, "assets/stages.yaml")
BRAINMASK = "brainMask_fused.nii.gz"
BRAINMASK_BAK = ".brainMask_fused.nii.gz"
REVIEW_FILENAME = "review_cases.tar.gz"
REVIEWED_FILENAME = "reviewed_cases.tar.gz"
REVIEW_COMMAND = "itksnap"
REVIEW_COMMAND_WARNING = "ITK-Snap command-line-tools were not found in your system"
MANUAL_REVIEW_STAGE = 5
DONE_STAGE = 8
LISTITEM_MAX_LEN = 30

REVIEWED_PATTERN = r".*\/(.*)\/(.*)\/finalized\/(.*\.nii\.gz)"
BRAINMASK_PATTERN = r".*\/(.*)\/(.*)\/brainMask_fused.nii.gz"

ANNOTATIONS_ENABLED = False
ANNOTATIONS_DISABLED_WARNING = "Annotations through the monitoring tool are currently disabled"
