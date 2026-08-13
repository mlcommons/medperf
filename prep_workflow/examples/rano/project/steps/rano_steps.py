"""RANO stages wrapped as workflow ``Step`` classes.

Each class does exactly what the reference ``direct_stages.py`` command did:
construct the reused scientific stage from ``stages/`` and call its per-subject
``execute(index)`` (or the dataset-level method for barriers). The heavy imports
are done lazily inside ``run`` so the workflow can be inspected/validated without
the scientific dependencies (which live in the ``mlcommons/rano-data-prep-mlcube``
base image). Flow/branching is decided by ``workflow.yaml`` + the ``conditions``
package, not by the stages themselves.
"""

import os

from prep_workflow import Step


def _index(subject: str) -> str:
    # engine subject id "subjectID/timepoint" -> reference index "subjectID|timepoint"
    from stages.utils import convert_path_to_index

    return convert_path_to_index(subject)


class Setup(Step):
    """Barrier: reorganize raw input, initialize the report, and register subjects."""

    per_subject = False

    def run(self, ctx):
        from stages.env_vars import DATA_DIR, INPUT_DIR, WORKSPACE_DIR
        from stages.generate_report import InitialSetup
        from stages.mlcube_constants import (
            BRAIN_PATH,
            BRAIN_STAGE_STATUS,
            DONE_STAGE_STATUS,
            LABELS_PATH,
            MANUAL_STAGE_STATUS,
            RAW_PATH,
            TUMOR_PATH,
        )

        InitialSetup(
            data_csv=None,
            input_path=INPUT_DIR,
            output_path=os.path.join(DATA_DIR, RAW_PATH),
            input_labels_path=INPUT_DIR,
            output_labels_path=os.path.join(WORKSPACE_DIR, LABELS_PATH),
            done_data_out_path=DATA_DIR,
            done_status=DONE_STAGE_STATUS,
            brain_data_out_path=os.path.join(DATA_DIR, BRAIN_PATH),
            brain_status=BRAIN_STAGE_STATUS,
            tumor_data_out_path=os.path.join(DATA_DIR, TUMOR_PATH),
            reviewed_status=MANUAL_STAGE_STATUS,
        ).execute(None)

        # register one subject per <subject>/<timepoint> so the engine can fan out
        for subject in sorted(os.listdir(INPUT_DIR)):
            subject_path = os.path.join(INPUT_DIR, subject)
            if not os.path.isdir(subject_path):
                continue
            for timepoint in sorted(os.listdir(subject_path)):
                if os.path.isdir(os.path.join(subject_path, timepoint)):
                    ctx.report.add_subject(f"{subject}/{timepoint}")


class MakeCsv(Step):
    def run(self, ctx):
        from stages.env_vars import DATA_DIR, INPUT_DIR
        from stages.get_csv import AddToCSV
        from stages.mlcube_constants import VALID_PATH
        from stages.utils import get_aux_files_dir, get_data_csv_filepath

        os.makedirs(get_aux_files_dir(ctx.subject), exist_ok=True)
        AddToCSV(
            input_dir=INPUT_DIR,
            output_csv=get_data_csv_filepath(ctx.subject),
            out_dir=os.path.join(DATA_DIR, VALID_PATH),
            prev_stage_path=INPUT_DIR,
        ).execute(_index(ctx.subject))


class ConvertNifti(Step):
    def run(self, ctx):
        from stages.env_vars import DATA_DIR, INPUT_DIR, WORKSPACE_DIR
        from stages.mlcube_constants import METADATA_PATH, PREP_PATH
        from stages.nifti_transform import NIfTITransform
        from stages.utils import get_data_csv_filepath

        output_path = os.path.join(DATA_DIR, PREP_PATH, ctx.subject)
        metadata_path = os.path.join(WORKSPACE_DIR, METADATA_PATH)
        os.makedirs(output_path, exist_ok=True)
        os.makedirs(metadata_path, exist_ok=True)
        NIfTITransform(
            data_csv=get_data_csv_filepath(ctx.subject),
            out_path=output_path,
            prev_stage_path=INPUT_DIR,
            metadata_path=metadata_path,
            data_out=DATA_DIR,
        ).execute(_index(ctx.subject))


class BrainExtraction(Step):
    def run(self, ctx):
        from stages.constants import INTERIM_FOLDER
        from stages.env_vars import DATA_DIR
        from stages.extract import Extract
        from stages.mlcube_constants import BRAIN_PATH, BRAIN_STAGE_STATUS, PREP_PATH
        from stages.utils import get_data_csv_filepath

        output_path = os.path.join(DATA_DIR, BRAIN_PATH, ctx.subject)
        os.makedirs(output_path, exist_ok=True)
        Extract(
            data_csv=get_data_csv_filepath(ctx.subject),
            out_path=output_path,
            subpath=INTERIM_FOLDER,
            prev_stage_path=os.path.join(DATA_DIR, PREP_PATH, ctx.subject),
            prev_subpath=INTERIM_FOLDER,
            func_name="extract_brain",
            status_code=BRAIN_STAGE_STATUS,
        ).execute(_index(ctx.subject))


class TumorExtraction(Step):
    def run(self, ctx):
        from stages.constants import INTERIM_FOLDER
        from stages.env_vars import DATA_DIR, WORKSPACE_DIR
        from stages.extract_nnunet import ExtractNnUNet
        from stages.mlcube_constants import BRAIN_PATH, TUMOR_PATH, TUMOR_STAGE_STATUS
        from stages.utils import get_data_csv_filepath

        output_path = os.path.join(DATA_DIR, TUMOR_PATH, ctx.subject)
        os.makedirs(output_path, exist_ok=True)
        models_path = os.path.join(WORKSPACE_DIR, "additional_files", "models")
        tmpfolder = os.path.join(WORKSPACE_DIR, DATA_DIR, ".tmp", ctx.subject)
        cbica_tmpfolder = os.path.join(tmpfolder, ".cbicaTemp")
        os.makedirs(tmpfolder, exist_ok=True)
        os.makedirs(cbica_tmpfolder, exist_ok=True)
        os.environ["TMPDIR"] = tmpfolder
        os.environ["CBICA_TEMP_DIR"] = cbica_tmpfolder
        os.environ["RESULTS_FOLDER"] = os.path.join(
            models_path, "nnUNet_trained_models"
        )
        os.environ["nnUNet_raw_data_base"] = os.path.join(
            tmpfolder, "nnUNet_raw_data_base"
        )
        os.environ["nnUNet_preprocessed"] = os.path.join(
            tmpfolder, "nnUNet_preprocessed"
        )
        ExtractNnUNet(
            data_csv=get_data_csv_filepath(ctx.subject),
            out_path=output_path,
            subpath=INTERIM_FOLDER,
            prev_stage_path=os.path.join(DATA_DIR, BRAIN_PATH, ctx.subject),
            prev_subpath=INTERIM_FOLDER,
            status_code=TUMOR_STAGE_STATUS,
        ).execute(_index(ctx.subject))


def _manual_stage(subject):
    from stages.env_vars import DATA_DIR, WORKSPACE_DIR
    from stages.manual import ManualStage
    from stages.mlcube_constants import LABELS_PATH, TUMOR_BACKUP_PATH, TUMOR_PATH
    from stages.utils import get_data_csv_filepath

    prev_stage_path = os.path.join(DATA_DIR, TUMOR_PATH, subject)
    return ManualStage(
        data_csv=get_data_csv_filepath(subject),
        out_path=prev_stage_path,
        prev_stage_path=prev_stage_path,
        backup_path=os.path.join(WORKSPACE_DIR, LABELS_PATH, TUMOR_BACKUP_PATH),
    )


class PrepareForReview(Step):
    def run(self, ctx):
        _manual_stage(ctx.subject).prepare_directories(_index(ctx.subject))


class Rollback(Step):
    def run(self, ctx):
        _manual_stage(ctx.subject).rollback(_index(ctx.subject))


class SegmentationComparison(Step):
    def run(self, ctx):
        from stages.comparison import SegmentationComparisonStage
        from stages.env_vars import DATA_DIR, WORKSPACE_DIR
        from stages.mlcube_constants import LABELS_PATH, TUMOR_BACKUP_PATH, TUMOR_PATH
        from stages.utils import get_data_csv_filepath

        labels_out = os.path.join(WORKSPACE_DIR, LABELS_PATH)
        SegmentationComparisonStage(
            data_csv=get_data_csv_filepath(ctx.subject),
            out_path=labels_out,
            prev_stage_path=os.path.join(DATA_DIR, TUMOR_PATH, ctx.subject),
            backup_path=os.path.join(labels_out, TUMOR_BACKUP_PATH),
        ).execute(_index(ctx.subject))


def _confirm_stage():
    from stages.confirm import ConfirmStage
    from stages.env_vars import DATA_DIR, WORKSPACE_DIR
    from stages.mlcube_constants import LABELS_PATH, TUMOR_BACKUP_PATH, TUMOR_PATH

    labels_out = os.path.join(WORKSPACE_DIR, LABELS_PATH)
    return ConfirmStage(
        out_data_path=DATA_DIR,
        out_labels_path=labels_out,
        prev_stage_path=os.path.join(DATA_DIR, TUMOR_PATH),
        backup_path=os.path.join(labels_out, TUMOR_BACKUP_PATH),
    )


class CalculateChangedVoxels(Step):
    per_subject = False

    def run(self, ctx):
        _confirm_stage().execute()


class MoveLabeledFiles(Step):
    per_subject = False

    def run(self, ctx):
        _confirm_stage().move_labels()


class Consolidate(Step):
    per_subject = False

    def run(self, ctx):
        from stages.constants import INTERIM_FOLDER
        from stages.env_vars import DATA_DIR, WORKSPACE_DIR
        from stages.mlcube_constants import (
            AUX_FILES_PATH,
            BRAIN_PATH,
            LABELS_PATH,
            MANUAL_REVIEW_PATH,
            PREP_PATH,
            RAW_PATH,
            TUMOR_PATH,
            VALID_PATH,
        )
        from stages.split import SplitStage

        labels_out = os.path.join(WORKSPACE_DIR, LABELS_PATH)
        subdirs = [
            BRAIN_PATH,
            AUX_FILES_PATH,
            PREP_PATH,
            TUMOR_PATH,
            RAW_PATH,
            VALID_PATH,
            MANUAL_REVIEW_PATH,
        ]
        dirs_to_remove = [os.path.join(DATA_DIR, s) for s in subdirs]
        dirs_to_remove += [
            os.path.join(WORKSPACE_DIR, DATA_DIR, ".tmp"),
            os.path.join(labels_out, ".tmp"),
            os.path.join(labels_out, ".tumor_segmentation_backup"),
        ]
        SplitStage(
            params=os.path.join(WORKSPACE_DIR, "parameters.yaml"),
            data_path=DATA_DIR,
            labels_path=labels_out,
            staging_folders=dirs_to_remove,
            base_finalized_dir=os.path.join(DATA_DIR, TUMOR_PATH, INTERIM_FOLDER),
        ).execute()


class SanityCheck(Step):
    """First step of the `statistics` task, Invoked by (--start=sanity_check). Fail if any subject is empty."""

    per_subject = False

    def run(self, ctx):
        from sanity_check import sanity_check
        from stages.env_vars import DATA_DIR, WORKSPACE_DIR
        from stages.mlcube_constants import LABELS_PATH

        sanity_check(
            data_path=DATA_DIR,
            labels_path=os.path.join(WORKSPACE_DIR, LABELS_PATH),
        )


class Statistics(Step):
    """`statistics` step: writes to the MedPerf statistics mount."""

    per_subject = False

    def run(self, ctx):
        from metrics import calculate_statistics
        from stages.env_vars import DATA_DIR, WORKSPACE_DIR
        from stages.mlcube_constants import METADATA_PATH

        calculate_statistics(
            os.path.join(DATA_DIR, "splits.csv"),
            os.path.join(WORKSPACE_DIR, METADATA_PATH, ".invalid.txt"),
            ctx.paths.statistics_file,
        )
