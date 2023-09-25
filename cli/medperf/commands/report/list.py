from tabulate import tabulate

from medperf import config
from medperf.exceptions import InvalidArgumentError


class ListReports:
    @staticmethod
    def run(benchmark_uid: int = None, mlcube_uid: int = None, mine: bool = False):
        """Get reports"""
        comms = config.comms
        ui = config.ui

        if bool(benchmark_uid) + bool(mlcube_uid) + mine > 1:
            # You can only choose one filter at a time
            InvalidArgumentError("Can't pass more than one filter at a time")

        if mine:
            reports = comms.get_user_reports()
        elif benchmark_uid:
            reports = comms.get_benchmark_reports(benchmark_uid)
        elif mlcube_uid:
            reports = comms.get_mlcube_reports(mlcube_uid)
        else:
            reports = comms.get_reports()

        headers = ["Report ID", "Dataset Name", "MLCube UID", "Benchmark UID", "Status"]

        reports_info = []
        for report in reports:
            report_text = "\n".join(
                [f"{k}: {v}" for k, v in report["contents"].items()]
            )
            report_info = (
                report["id"],
                report["dataset_name"],
                report["data_preparation_mlcube"],
                report["benchmark"],
                report_text,
            )
            reports_info.append(report_info)

        tab = tabulate(reports_info, headers=headers, tablefmt="grid")
        ui.print(tab)
