import os


def stage_id2name(stage_str, stages_df):
    _, code = stage_str.split()
    code = float(code)
    name = stages_df.loc[code, "status_name"]
    return name


def get_institution_from_email(email, user2institution):
    invalid_institutions = {"gmail.com", "hotmail.com", "yahoo.com", "outlook.com"}
    institution = user2institution.get(email, None)
    if institution is not None:
        return institution
    plausible_institution = email.split("@")[1]
    if plausible_institution in invalid_institutions:
        return email
    else:
        return plausible_institution


def get_reports_path(out_path, benchmark_id):
    full_path = os.path.join(out_path, str(benchmark_id))
    return full_path
