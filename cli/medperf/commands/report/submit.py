import os
import yaml

from medperf import config
from medperf.utils import dict_pretty_print, approval_prompt, storage_path


class ReportRegistration:
    @staticmethod
    def run(in_data_hash: str, prep_cube_uid: int, benchmark_uid: int, approved=False):
        """Registers a report

        Args:
            in_data_hash (str): Input data hash, to identify the report
            prep_cube_uid (int): Data Preparation Cube UID, to identify the report
            benchmark_uid (int): Benchmark UID, to submit report to
            approved (bool, optional): Submission pre-approval. Skipps approval procedure. Defaults to False.
        """
        comms = config.comms
        ui = config.ui
        report_uid = None

        staging_path = storage_path(config.staging_data_storage)
        out_path = os.path.join(staging_path, f"{in_data_hash}_{prep_cube_uid}")
        report_path = os.path.join(out_path, config.report_file)
        report_metadata_path = os.path.join(out_path, config.report_metadata_file)

        with open(report_path, "r") as f:
            report = yaml.safe_load(f)

        # del report["path"]
        del report["comment"]

        if os.path.exists(report_metadata_path):
            with open(report_metadata_path, "r") as f:
                metadata = yaml.safe_load(f)
            report_uid = metadata["id"]
            approved = True

        if report_uid is None:
            dict_pretty_print(report)
            msg = (
                "Do you approve the submission of the status report to the MedPerf Server?"
                + " This report will be visible by the benchmark owner and updated in subsequent calls"
                + " [Y/n]"
            )

            approved = approved or approval_prompt(msg)

        if not approved:
            ui.print("Report submission cancelled")
            return

        ui.print("Uploading report")

        body = {
            "benchmark_id": benchmark_uid,
            "dataset_input_hash": in_data_hash,
            "report": report,
        }

        if report_uid is not None:
            report_metadata = comms.update_report(report_uid, body)
        else:
            report_metadata = comms.upload_report(body)

        with open(report_metadata_path, "w") as f:
            yaml.dump(report_metadata, f)
