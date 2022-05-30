from pathlib import Path
import shutil


def copy_subject(subject_dir: Path, output_dir_data: Path, output_dir_labels: Path):
    subj_id = subject_dir.name
    # it's possible that minor naming differences are present. Accepted options for each modality are below.
    # input format:
    # <subject_id>[_brain]_t1.nii.gz etc
    # <subject_id>[_brain]_final_seg.nii.gz
    # output format:
    # <subject_id>_brain_t1.nii.gz etc
    # <subject_id>_final_seg.nii.gz
    files_to_copy = {
        "t1": [f"{subj_id}_brain_t1.nii.gz", f"{subj_id}_t1.nii.gz"],
        "t1ce": [f"{subj_id}_brain_t1ce.nii.gz", f"{subj_id}_t1ce.nii.gz"],
        "t2": [f"{subj_id}_brain_t2.nii.gz", f"{subj_id}_t2.nii.gz"],
        "flair": [f"{subj_id}_brain_flair.nii.gz", f"{subj_id}_flair.nii.gz"],
        "seg": [
            f"{subj_id}_final_seg.nii.gz",
            f"{subj_id}_brain_final_seg.nii.gz",
            f"{subj_id}_seg.nii.gz",
            f"{subj_id}_brain_seg.nii.gz",
        ],
    }
    for k, fname_options in files_to_copy.items():
        for filename in fname_options:
            file_path = subject_dir / filename
            output_dir = output_dir_data / subj_id
            if k == "seg":
                output_dir = output_dir_labels
            output_dir.mkdir(exist_ok=True)
            if file_path.exists():
                shutil.copy2(file_path, output_dir / files_to_copy[k][0])
                break


def run_preparation(
    input_dir: str, output_data_dir: str, output_label_dir: str
) -> None:
    output_data_path = Path(output_data_dir)
    output_labels_path = Path(output_label_dir)
    output_data_path.mkdir(parents=True, exist_ok=True)
    output_labels_path.mkdir(parents=True, exist_ok=True)

    for subject_dir in Path(input_dir).iterdir():
        if subject_dir.is_dir():
            copy_subject(subject_dir, output_data_path, output_labels_path)
