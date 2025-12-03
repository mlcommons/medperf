# check against all these modality ID strings with extensions
MODALITY_ID_DICT = {
    "T1": ["t1", "t1pre", "t1precontrast", "t1n"],
    "T1GD": ["t1ce", "t1gd", "t1post", "t1postcontrast", "t1gallodinium", "t1c"],
    "T2": ["t2", "t2w"],
    "FLAIR": ["flair", "fl", "t2flair", "t2f"],
}
# this is used to keep a mapping between the fets1 nomenclature
MODALITY_ID_MAPPING = {
    "T1": "t1n",
    "T1GD": "t1c",
    "T2": "t2w",
    "FLAIR": "t2f",
}
MODALITIES_LIST = list(MODALITY_ID_DICT.keys())
SUBJECT_NAMES = {"patientid", "subjectid", "subject", "subid"}
TIMEPOINT_NAMES = {"timepoint", "tp", "time", "series", "subseries"}
INPUT_FILENAMES = {
    "T1": "T1_to_SRI.nii.gz",
    "T1GD": "T1CE_to_SRI.nii.gz",
    "T2": "T2_to_SRI.nii.gz",
    "FLAIR": "FL_to_SRI.nii.gz",
}

GANDLF_DF_COLUMNS = ["SubjectID", "Channel_0"]

INTERIM_FOLDER = "DataForQC"
FINAL_FOLDER = "DataForFeTS"
TUMOR_MASK_FOLDER = "TumorMasksForQC"
TESTING_FOLDER = "testing"
REORIENTED_FOLDER = "reoriented"

BRAIN_FILENAME = "gandlf_brain_extraction.csv"
TUMOR_FILENAME = "gandlf_tumor_segmentation.csv"
SUBJECTS_FILENAME = "processed_data.csv"
NEG_SUBJECTS_FILENAME = "QC_subjects_with_negative_intensities.csv"
FAIL_SUBJECTS_FILENAME = "QC_subjects_with_bratspipeline_error.csv"
DICOM_ANON_FILENAME = "dicom_tag_information_to_write_anon.yaml"
DICOM_COLLAB_FILENAME = "dicom_tag_information_to_write_collab.yaml"
STDOUT_FILENAME = "preparedataset_stdout.txt"
STDERR_FILENAME = "preparedataset_stderr.txt"

EXEC_NAME = "BraTSPipeline"
