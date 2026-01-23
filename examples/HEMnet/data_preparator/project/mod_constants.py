from pathlib import Path
import SimpleITK as sitk

BASE_DIR = Path("/workspace")
INPUT_PATH = BASE_DIR.joinpath("input_data")
OUTPUT_PATH = BASE_DIR.joinpath("data")
TEMP_DATA_PATH = OUTPUT_PATH.joinpath(".tmp")
NORMALISER_PKL = "normaliser.pkl"
AFFINE_TRANSFORM_HDF = "affine_transform.hdf"
MOVING_RESAMPLED_AFFINE_NPY = "moving_resampled_affine.npy"
TP53_FILTERED_NPY = "tp53_filtered.npy"
HE_FILTERED_NPY = "he_filtered.npy"
INTERPOLATOR = sitk.sitkLanczosWindowedSinc
U_MASK_FILTERED = "u_mask_filtered.npy"
C_MASK_FILTERED = "c_mask_filtered.npy"
NON_C_MASK_FILTERED = "non_c_mask_filtered.npy"
T_MASK_FILTERED = "t_mask_filtered.npy"
HE_NORM = "he_norm.npy"
HE_GRAY = "he_gray.npy"
TP53_GRAY = "tp53_gray.npy"
PERFORMANCE_DF = "performance_metrics.csv"
