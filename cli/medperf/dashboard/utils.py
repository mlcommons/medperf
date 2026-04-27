import os

from medperf.utils import sanitize_path


def get_reports_path(out_path, benchmark_id):
    """Directory used to store and read dashboard CSV artifacts for a benchmark."""
    full_path = os.path.join(str(out_path), str(benchmark_id))
    return sanitize_path(full_path)


def get_institution_from_email(email, user2institution):
    """Resolve institution label from user email using the institutions CSV mapping."""
    return user2institution.get(email, email)


def stage_id2name(stage_key, stages_df):
    """Map a progress/status code from dataset reports to the human-readable stage name."""
    try:
        if stage_key in stages_df.index and "status_name" in stages_df.columns:
            return str(stages_df.loc[stage_key, "status_name"])
    except (KeyError, TypeError, ValueError):
        pass
    return str(stage_key)
