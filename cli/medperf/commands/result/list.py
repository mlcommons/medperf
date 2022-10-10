from tabulate import tabulate

from medperf import config
from medperf.ui.interface import UI
from medperf.comms.interface import Comms
from medperf.entities.result import Result


class ResultsList:
    @staticmethod
    def run(comms: Comms = config.comms, ui: UI = config.ui):
        """Lists all local datasets

        Args:
            comms (Comms, optional): Communications instance. Defaults to config.comms
            ui (UI, optional): UI instance. Defaults to config.ui
        """
        results = Result.all()
        headers = ["Benchmark UID", "Model UID", "Data UID", "Submitted", "Local"]
        # Get local results data
        results_data = [
            [
                result.benchmark_uid,
                result.model_uid,
                result.dataset_uid,
                result.uid is not None,
                True,
            ]
            for result in results
        ]
        local_uids = [result.uid for result in results]

        # Get remote results data
        remote_results = comms.get_user_results()
        remote_results_data = [
            [result["benchmark"], result["model"], result["dataset"], True, False]
            for result in remote_results
            if result["id"] not in local_uids
        ]
        results_data += remote_results_data
        tab = tabulate(results_data, headers=headers)
        ui.print(tab)
