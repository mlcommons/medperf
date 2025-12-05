import os


def annotation_done(pipeline_state):

    base_review_dir = os.path.join(
        pipeline_state.host_output_data_path,
        "manual_review",
        "tumor_extraction",
        pipeline_state.running_subject,
    )
    finalized_dir = os.path.join(base_review_dir, "finalized")
    dir_files = os.listdir(finalized_dir)

    if len(dir_files) == 0:
        print("Reviewed annotation not Found!")
        return False

    elif len(dir_files) > 1:
        print(
            "More than one annotation found! Please only keep one file in the finalized directory"
        )
        return False

    formatted_subject = pipeline_state.running_subject.replace("/", "_")
    proper_name = f"{formatted_subject}_tumorMask_model_0.nii.gz"
    if dir_files[0] != proper_name:
        print(
            f"Reviewed file has been renamed! Please make sure the file is named\n{proper_name}\nto ensure the pipeline runs correctly!"
        )
        return False
    return True


def brain_mask_changed(pipeline_state):

    base_review_dir = os.path.join(
        pipeline_state.host_output_data_path,
        "manual_review",
        "brain_mask",
        pipeline_state.running_subject,
    )
    finalized_dir = os.path.join(base_review_dir, "finalized")
    dir_files = os.listdir(finalized_dir)

    if len(dir_files) == 0:
        print("No brain mask change detected.")
        return False

    elif len(dir_files) > 1:
        print(
            "More than one brain mask correction found! Please only keep one file in the finalized directory."
        )
        return False

    proper_name = f"brainMask_fused.nii.gz"
    if dir_files[0] != proper_name:
        print(
            f"Brain Mask file has been renamed! Please make sure the file is named\n{proper_name}\nto ensure the pipeline runs correctly!"
        )
        return False
    return True
