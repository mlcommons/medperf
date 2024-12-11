import os
import shutil
import argparse
import pandas as pd
import yaml
from stages.generate_report import GenerateReport
from stages.get_csv import AddToCSV
from stages.nifti_transform import NIfTITransform
from stages.extract import Extract
from stages.extract_nnunet import ExtractNnUNet
from stages.manual import ManualStage
from stages.comparison import SegmentationComparisonStage
from stages.confirm import ConfirmStage
from stages.split import SplitStage
from stages.pipeline import Pipeline
from stages.mlcube_constants import *
from stages.constants import INTERIM_FOLDER, FINAL_FOLDER, TUMOR_MASK_FOLDER

def find_csv_filenames(path_to_dir, suffix=".csv"):
    filenames = os.listdir(path_to_dir)
    return [filename for filename in filenames if filename.endswith(suffix)]


def setup_argparser():
    parser = argparse.ArgumentParser("Medperf Data Preparator Example")
    parser.add_argument(
        "--data_path", dest="data", type=str, help="path containing raw data"
    )
    parser.add_argument(
        "--labels_path", dest="labels", type=str, help="path containing labels"
    )
    parser.add_argument(
        "--models_path", dest="models", type=str, help="path to the nnunet models"
    )
    parser.add_argument(
        "--data_out", dest="data_out", type=str, help="path to store prepared data"
    )
    parser.add_argument(
        "--labels_out",
        dest="labels_out",
        type=str,
        help="path to store prepared labels",
    )
    parser.add_argument(
        "--report", dest="report", type=str, help="path to the report csv file to store"
    )
    parser.add_argument(
        "--parameters",
        dest="parameters",
        type=str,
        help="path to the parameters yaml file",
    )
    parser.add_argument(
        "--metadata_path",
        dest="metadata_path",
        type=str,
        help="path to the local metadata folder"
    )

    return parser.parse_args()


def init_pipeline(args):
    # RUN COLUMN-WISE PROCESSING
    out_raw = os.path.join(args.data_out, RAW_PATH)
    valid_data_out = os.path.join(args.data_out, VALID_PATH)
    nifti_data_out = os.path.join(args.data_out, PREP_PATH)
    brain_data_out = os.path.join(args.data_out, BRAIN_PATH)
    tumor_data_out = os.path.join(args.data_out, TUMOR_PATH)
    match_data_out = args.labels_out
    backup_out = os.path.join(args.labels_out, TUMOR_BACKUP_PATH)
    staging_folders = [
        out_raw,
        valid_data_out,
        nifti_data_out,
        brain_data_out,
        tumor_data_out,
        backup_out,
    ]
    out_data_csv = os.path.join(args.data_out, OUT_CSV)
    trash_folder = os.path.join(args.data_out, TRASH_PATH)
    invalid_subjects_file = os.path.join(args.metadata_path, INVALID_FILE)

    loop = None
    report_gen = GenerateReport(
        out_data_csv,
        args.data,
        out_raw,
        args.labels,
        args.labels_out,
        args.data_out,
        DONE_STAGE_STATUS,
        brain_data_out,
        BRAIN_STAGE_STATUS,
        tumor_data_out,
        MANUAL_STAGE_STATUS\
    )
    csv_proc = AddToCSV(out_raw, out_data_csv, valid_data_out, out_raw)
    nifti_proc = NIfTITransform(out_data_csv, nifti_data_out, valid_data_out, args.metadata_path, args.data_out)
    brain_extract_proc = Extract(
        out_data_csv,
        brain_data_out,
        INTERIM_FOLDER,
        nifti_data_out,
        INTERIM_FOLDER,
        # loop,
        "extract_brain",
        BRAIN_STAGE_STATUS,
    )
    tumor_extract_proc = ExtractNnUNet(
        out_data_csv,
        tumor_data_out,
        INTERIM_FOLDER,
        brain_data_out,
        INTERIM_FOLDER,
        TUMOR_STAGE_STATUS,
    )
    manual_proc = ManualStage(out_data_csv, tumor_data_out, tumor_data_out, backup_out)
    match_proc = SegmentationComparisonStage(
        out_data_csv,
        match_data_out,
        tumor_data_out,
        backup_out,
    )
    confirm_proc = ConfirmStage(
        out_data_csv,
        args.data_out,
        args.labels_out,
        tumor_data_out,
        backup_out,
        staging_folders,
    )
    split_proc = SplitStage(
        args.parameters, args.data_out, args.labels_out, staging_folders
    )
    stages = [
        csv_proc,
        nifti_proc,
        brain_extract_proc,
        tumor_extract_proc,
        manual_proc,
        match_proc,
        confirm_proc,
        split_proc
    ]
    return Pipeline(report_gen, stages, staging_folders, [trash_folder], invalid_subjects_file)

def init_report(args) -> pd.DataFrame:
    report = None
    if os.path.exists(args.report):
        with open(args.report, "r") as f:
            report_data = yaml.safe_load(f)
        report = pd.DataFrame(report_data)

    return report


def main():
    args = setup_argparser()

    output_path = args.data_out
    models_path = args.models

    tmpfolder = os.path.join(output_path, ".tmp")
    cbica_tmpfolder = os.path.join(tmpfolder, ".cbicaTemp")
    os.environ["TMPDIR"] = tmpfolder
    os.environ["CBICA_TEMP_DIR"] = cbica_tmpfolder
    os.makedirs(tmpfolder, exist_ok=True)
    os.makedirs(cbica_tmpfolder, exist_ok=True)
    os.environ["RESULTS_FOLDER"] = os.path.join(models_path, "nnUNet_trained_models")
    os.environ["nnUNet_raw_data_base"] = os.path.join(tmpfolder, "nnUNet_raw_data_base")
    os.environ["nnUNet_preprocessed"] = os.path.join(tmpfolder, "nnUNet_preprocessed")

    report = init_report(args)
    pipeline = init_pipeline(args)
    pipeline.run(report, args.report)

    # cleanup tmp folder
    shutil.rmtree(tmpfolder, ignore_errors=True)

if __name__ == "__main__":
    main()