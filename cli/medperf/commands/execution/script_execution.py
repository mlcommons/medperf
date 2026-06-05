import os
import logging

from medperf.entities.cube import Cube
from medperf.entities.asset import Asset
from medperf.entities.dataset import Dataset
from medperf.entities.execution import Execution
from medperf.utils import remove_path
import medperf.config as config
from medperf.exceptions import ExecutionError, CommunicationError, CleanExit
import yaml
from time import time


class ScriptExecution:
    @classmethod
    def run(
        cls,
        dataset: Dataset,
        model: Asset,
        script: Cube,
        execution: Execution = None,
        ignore_model_errors=False,
    ):
        """Benchmark execution flow.

        Args:
            benchmark_uid (int): UID of the desired benchmark
            data_uid (str): Registered Dataset UID
            model_uid (int): UID of model to execute
        """
        execution_flow = cls(dataset, model, script, execution, ignore_model_errors)
        execution_flow.prepare()
        with execution_flow.ui.interactive():
            execution_flow.set_pending_status()
            execution_flow.run_script()
        execution_summary = execution_flow.todict()
        return execution_summary

    def __init__(
        self,
        dataset: Dataset,
        model: Asset,
        script: Cube,
        execution: Execution = None,
        ignore_model_errors=False,
    ):
        self.comms = config.comms
        self.ui = config.ui
        self.dataset = dataset
        self.model = model
        self.script = script
        self.execution = execution
        self.ignore_model_errors = ignore_model_errors

    def prepare(self):
        self.results_path = self.__setup_results_path()
        self.logs_path = self.__setup_logs_path()

    def __setup_logs_path(self):
        model_uid = self.model.local_id
        script_uid = self.script.local_id
        data_uid = self.dataset.local_id

        logs_path = os.path.join(
            config.experiments_logs_folder, str(model_uid), str(data_uid)
        )
        os.makedirs(logs_path, exist_ok=True)
        logs_path = os.path.join(logs_path, f"script_{script_uid}.log")
        return logs_path

    def __setup_results_path(self):
        if self.execution is not None and self.execution.id is not None:
            timestamp = str(time()).replace(".", "_")
            results_path = os.path.join(
                config.script_result_folder, str(self.execution.id), timestamp
            )
        else:
            # for compatibility test execution flows
            model_uid = self.model.local_id
            data_uid = self.dataset.local_id
            results_path = os.path.join(
                config.script_result_folder, str(model_uid), str(data_uid)
            )
            remove_path(results_path)  # clear it

        return results_path

    def set_pending_status(self):
        self.__send_report("pending")

    def run_script(self):
        self.ui.text = "Running benchmark script"
        script_timeout = config.evaluate_timeout
        script_mounts = {
            "data_path": self.dataset.data_path,
            "labels_path": self.dataset.labels_path,
            "model_files": self.model.asset_files_path,
            "results_path": self.results_path,
        }
        self.__send_report("started")
        try:
            self.script.run(
                task="run_script",
                output_logs=self.logs_path,
                timeout=script_timeout,
                mounts=script_mounts,
                env={"MEDPERF_ON_PREM": "1"},
            )
        except ExecutionError as e:
            logging.error(f"Script run failed: {e}")
            self.__send_report("failed")
            raise ExecutionError(f"Script run failed: {e}")
        except KeyboardInterrupt:
            logging.warning("Script run interrupted by user")
            self.__send_report("interrupted")
            raise CleanExit("Script run interrupted by user")
        self.__send_report("finished")

    def todict(self):
        return {
            "results": self.get_results(),
            "partial": False,
        }

    def get_results(self):
        if not os.path.exists(self.results_path):
            raise ExecutionError("Results folder does not exist")
        results_file = os.path.join(self.results_path, config.results_filename)
        if not os.path.exists(results_file):
            return {}

        with open(results_file, "r") as f:
            results = yaml.safe_load(f)
        if results is None:
            return {}
        return results

    def __send_report(self, status: str):
        if self.execution is None or self.execution.id is None:
            return

        execution_id = self.execution.id
        body = {"script_report": {"execution_status": status}}
        try:
            config.comms.update_execution(execution_id, body)
        except CommunicationError as e:
            logging.error(str(e))
            return
