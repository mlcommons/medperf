"""MLCube handler file"""

import typer
import os
from stages.env_vars import WORKSPACE_DIR, DATA_DIR, INPUT_DIR
from stages.utils import get_aux_files_dir, get_data_csv_filepath, convert_path_to_index
from stages.mlcube_constants import (
    RAW_PATH,
    AUX_FILES_PATH,
    VALID_PATH,
    PREP_PATH,
    BRAIN_PATH,
    TUMOR_PATH,
    DONE_STAGE_STATUS,
    BRAIN_STAGE_STATUS,
    TUMOR_STAGE_STATUS,
    TUMOR_BACKUP_PATH,
    MANUAL_STAGE_STATUS,
    MANUAL_REVIEW_PATH,
    LABELS_PATH,
    METADATA_PATH,
)
from stages.constants import INTERIM_FOLDER
from sanity_check import sanity_check
from metrics import calculate_statistics

app = typer.Typer()


@app.command("initial_setup")
def initial_setup():
    from stages.generate_report import InitialSetup

    raw_dir = os.path.join(DATA_DIR, RAW_PATH)
    labels_out_dir = os.path.join(WORKSPACE_DIR, LABELS_PATH)
    brain_out = os.path.join(DATA_DIR, BRAIN_PATH)
    tumor_out = os.path.join(DATA_DIR, TUMOR_PATH)
    report_generator = InitialSetup(
        data_csv=None,
        input_path=INPUT_DIR,
        output_path=raw_dir,
        input_labels_path=INPUT_DIR,
        output_labels_path=labels_out_dir,
        done_data_out_path=DATA_DIR,
        done_status=DONE_STAGE_STATUS,
        brain_data_out_path=brain_out,
        brain_status=BRAIN_STAGE_STATUS,
        tumor_data_out_path=tumor_out,
        reviewed_status=MANUAL_STAGE_STATUS,
    )
    report_generator.execute(None)


@app.command("make_csv")
def prepare(
    subject_subdir: str = typer.Option(..., "--subject-subdir"),
):
    from stages.get_csv import (
        AddToCSV,
    )

    output_csv_dir = get_aux_files_dir(subject_subdir)
    os.makedirs(output_csv_dir, exist_ok=True)
    output_csv = get_data_csv_filepath(subject_subdir)
    out_dir = os.path.join(DATA_DIR, VALID_PATH)
    csv_creator = AddToCSV(
        input_dir=INPUT_DIR,
        output_csv=output_csv,
        out_dir=out_dir,
        prev_stage_path=INPUT_DIR,
    )
    subject_index = convert_path_to_index(subject_subdir)
    csv_creator.execute(subject_index)
    print(output_csv)


@app.command("convert_nifti")
def convert_nifti(
    subject_subdir: str = typer.Option(..., "--subject-subdir"),
):
    from stages.nifti_transform import NIfTITransform

    csv_path = get_data_csv_filepath(subject_subdir)
    output_path = os.path.join(DATA_DIR, PREP_PATH, subject_subdir)
    metadata_path = os.path.join(WORKSPACE_DIR, METADATA_PATH)
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(metadata_path, exist_ok=True)

    nifti_transform = NIfTITransform(
        data_csv=csv_path,
        out_path=output_path,
        prev_stage_path=INPUT_DIR,
        metadata_path=metadata_path,
        data_out=DATA_DIR,
    )
    subject_index = convert_path_to_index(subject_subdir)
    nifti_transform.execute(subject_index)
    print(output_path)


@app.command("extract_brain")
def extract_brain(
    subject_subdir: str = typer.Option(..., "--subject-subdir"),
):
    from stages.extract import Extract

    csv_path = get_data_csv_filepath(subject_subdir)
    output_path = os.path.join(DATA_DIR, BRAIN_PATH, subject_subdir)
    prev_path = os.path.join(DATA_DIR, PREP_PATH, subject_subdir)
    os.makedirs(output_path, exist_ok=True)

    brain_extract = Extract(
        data_csv=csv_path,
        out_path=output_path,
        subpath=INTERIM_FOLDER,
        prev_stage_path=prev_path,
        prev_subpath=INTERIM_FOLDER,
        func_name="extract_brain",
        status_code=BRAIN_STAGE_STATUS,
    )
    subject_index = convert_path_to_index(subject_subdir)
    brain_extract.execute(subject_index)
    print(output_path)


@app.command("extract_tumor")
def extract_tumor(
    subject_subdir: str = typer.Option(..., "--subject-subdir"),
):
    from stages.extract_nnunet import ExtractNnUNet

    csv_path = get_data_csv_filepath(subject_subdir)
    output_path = os.path.join(DATA_DIR, TUMOR_PATH, subject_subdir)
    prev_path = os.path.join(DATA_DIR, BRAIN_PATH, subject_subdir)
    os.makedirs(output_path, exist_ok=True)

    models_path = os.path.join(WORKSPACE_DIR, "additional_files", "models")
    tmpfolder = os.path.join(WORKSPACE_DIR, DATA_DIR, ".tmp", subject_subdir)
    cbica_tmpfolder = os.path.join(tmpfolder, ".cbicaTemp")
    os.environ["TMPDIR"] = tmpfolder
    os.environ["CBICA_TEMP_DIR"] = cbica_tmpfolder
    os.makedirs(tmpfolder, exist_ok=True)
    os.makedirs(cbica_tmpfolder, exist_ok=True)
    os.environ["RESULTS_FOLDER"] = os.path.join(models_path, "nnUNet_trained_models")
    os.environ["nnUNet_raw_data_base"] = os.path.join(tmpfolder, "nnUNet_raw_data_base")
    os.environ["nnUNet_preprocessed"] = os.path.join(tmpfolder, "nnUNet_preprocessed")
    tumor_extract = ExtractNnUNet(
        data_csv=csv_path,
        out_path=output_path,
        subpath=INTERIM_FOLDER,
        prev_stage_path=prev_path,
        prev_subpath=INTERIM_FOLDER,
        status_code=TUMOR_STAGE_STATUS,
    )
    subject_index = convert_path_to_index(subject_subdir)
    tumor_extract.execute(subject_index)
    print(output_path)


@app.command("prepare_for_manual_review")
def prepare_for_manual_review(
    subject_subdir: str = typer.Option(..., "--subject-subdir"),
):

    from stages.manual import ManualStage

    csv_path = get_data_csv_filepath(subject_subdir)
    prev_stage_path = os.path.join(DATA_DIR, TUMOR_PATH, subject_subdir)
    backup_out = os.path.join(WORKSPACE_DIR, LABELS_PATH, TUMOR_BACKUP_PATH)

    manual_validation = ManualStage(
        data_csv=csv_path,
        out_path=prev_stage_path,
        prev_stage_path=prev_stage_path,
        backup_path=backup_out,
    )
    subject_index = convert_path_to_index(subject_subdir)
    manual_validation.prepare_directories(subject_index)


@app.command("rollback_to_brain_extract")
def rollback(
    subject_subdir: str = typer.Option(..., "--subject-subdir"),
):

    from stages.manual import ManualStage

    csv_path = get_data_csv_filepath(subject_subdir)
    prev_stage_path = os.path.join(DATA_DIR, TUMOR_PATH, subject_subdir)
    backup_out = os.path.join(WORKSPACE_DIR, LABELS_PATH, TUMOR_BACKUP_PATH)

    manual_validation = ManualStage(
        data_csv=csv_path,
        out_path=prev_stage_path,
        prev_stage_path=prev_stage_path,
        backup_path=backup_out,
    )
    subject_index = convert_path_to_index(subject_subdir)
    manual_validation.rollback(subject_index)


@app.command("segmentation_comparison")
def segmentation_comparison(
    subject_subdir: str = typer.Option(..., "--subject-subdir"),
):
    from stages.comparison import SegmentationComparisonStage

    csv_path = get_data_csv_filepath(subject_subdir)
    prev_stage_path = os.path.join(DATA_DIR, TUMOR_PATH, subject_subdir)
    labels_out = os.path.join(WORKSPACE_DIR, LABELS_PATH)
    backup_out = os.path.join(labels_out, TUMOR_BACKUP_PATH)

    segment_compare = SegmentationComparisonStage(
        data_csv=csv_path,
        out_path=labels_out,
        prev_stage_path=prev_stage_path,
        backup_path=backup_out,
    )
    subject_index = convert_path_to_index(subject_subdir)
    segment_compare.execute(subject_index)


@app.command("calculate_changed_voxels")
def calculate_changed_voxels():
    from stages.confirm import ConfirmStage

    prev_stage_path = os.path.join(DATA_DIR, TUMOR_PATH)
    labels_out = os.path.join(WORKSPACE_DIR, LABELS_PATH)
    backup_out = os.path.join(labels_out, TUMOR_BACKUP_PATH)

    confirm_stage = ConfirmStage(
        out_data_path=DATA_DIR,
        out_labels_path=labels_out,
        prev_stage_path=prev_stage_path,
        backup_path=backup_out,
    )
    confirm_stage.execute()


@app.command("move_labeled_files")
def move_labeled_files():
    from stages.confirm import ConfirmStage

    prev_stage_path = os.path.join(DATA_DIR, TUMOR_PATH)
    labels_out = os.path.join(WORKSPACE_DIR, LABELS_PATH)
    backup_out = os.path.join(labels_out, TUMOR_BACKUP_PATH)

    confirm_stage = ConfirmStage(
        out_data_path=DATA_DIR,
        out_labels_path=labels_out,
        prev_stage_path=prev_stage_path,
        backup_path=backup_out,
    )
    confirm_stage.move_labels()


@app.command("consolidation_stage")
def consolidation_stage(keep_files: bool = typer.Option(False, "--keep-files")):
    from stages.split import SplitStage

    labels_out = os.path.join(WORKSPACE_DIR, LABELS_PATH)
    params_path = os.path.join(WORKSPACE_DIR, "parameters.yaml")
    base_finalized_dir = os.path.join(DATA_DIR, TUMOR_PATH, INTERIM_FOLDER)

    if keep_files:
        dirs_to_remove = []
    else:
        subdirs_to_remove = [
            BRAIN_PATH,
            AUX_FILES_PATH,
            PREP_PATH,
            TUMOR_PATH,
            RAW_PATH,
            TUMOR_PATH,
            VALID_PATH,
            MANUAL_REVIEW_PATH,
        ]
        dirs_to_remove = [
            os.path.join(DATA_DIR, subdir) for subdir in subdirs_to_remove
        ]
        dirs_to_remove.extend(
            [
                os.path.join(WORKSPACE_DIR, DATA_DIR, ".tmp"),
                os.path.join(labels_out, ".tmp"),
                os.path.join(labels_out, ".tumor_segmentation_backup"),
            ]
        )

    split = SplitStage(
        params=params_path,
        data_path=DATA_DIR,
        labels_path=labels_out,
        staging_folders=dirs_to_remove,
        base_finalized_dir=base_finalized_dir,
    )
    split.execute()


@app.command("sanity_check")
def sanity_check_cmdline():
    data_path = DATA_DIR
    labels_path = os.path.join(WORKSPACE_DIR, LABELS_PATH)
    sanity_check(data_path=data_path, labels_path=labels_path)


@app.command("metrics")
def metrics_cmdline():
    splits_path = os.path.join(DATA_DIR, "splits.csv")
    invalid_path = os.path.join(WORKSPACE_DIR, METADATA_PATH, ".invalid.txt")
    out_file = os.path.join(WORKSPACE_DIR, METADATA_PATH, "statistics.yml")
    calculate_statistics(splits_path, invalid_path, out_file)


if __name__ == "__main__":
    app()
