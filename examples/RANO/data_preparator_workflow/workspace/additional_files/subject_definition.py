import os


def subject_definition(pipeline_state):

    input_data_dir = os.getenv("host_data_path")
    subject_slash_timepoint_list = []

    for subject_id_dir in os.listdir(input_data_dir):
        subject_complete_dir = os.path.join(input_data_dir, subject_id_dir)

        if not os.path.isdir(subject_complete_dir):
            continue

        for timepoint_dir in os.listdir(subject_complete_dir):
            subject_slash_timepoint_list.append(
                os.path.join(subject_id_dir, timepoint_dir)
            )

    return subject_slash_timepoint_list
