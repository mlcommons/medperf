import yaml

from prep_workflow.report import DONE, Report


def test_roundtrip_and_medperf_shape(tmp_path):
    path = str(tmp_path / "report.yaml")
    report = Report(path)
    report.add_subject("s1")
    report.add_subject("s2")
    report.set_status("s1", 3, "brain_extraction")
    report.set_node("s1", "tumor")
    report.mark_done("s2")

    on_disk = yaml.safe_load(open(path))
    # column-oriented shape MedPerf reconstructs via pandas.DataFrame(report_dict)
    assert set(on_disk) >= {"status", "status_name", "node"}
    assert on_disk["status"]["s1"] == 3
    assert on_disk["node"]["s2"] == DONE

    # reloading recovers state (resume)
    reloaded = Report(path)
    reloaded.load()
    assert reloaded.get_node("s1") == "tumor"
    assert reloaded.is_done("s2")


def test_medperf_progress_summary(tmp_path):
    """The report must feed MedPerf's progress calculation without changes."""
    pd = __import__("importlib").util.find_spec("pandas")
    if pd is None:
        return  # pandas not installed in this env; shape test above still covers format
    import pandas as pd

    path = str(tmp_path / "report.yaml")
    report = Report(path)
    for s in ["s1", "s2", "s3", "s4"]:
        report.add_subject(s)
    report.set_status("s1", 2, "nifti")
    report.set_status("s2", 2, "nifti")
    report.set_status("s3", 1, "csv")
    report.set_status("s4", 1, "csv")

    report_dict = yaml.safe_load(open(path))
    df = pd.DataFrame(report_dict)
    counts = (df.status.value_counts() / len(df)).round(3).to_dict()
    assert counts[2] == 0.5 and counts[1] == 0.5


def test_error_status_is_negative(tmp_path):
    path = str(tmp_path / "report.yaml")
    report = Report(path)
    report.add_subject("s1")
    report.set_error("s1", 4, "tumor", "traceback here")
    assert yaml.safe_load(open(path))["status"]["s1"] == -4
