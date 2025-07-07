import os
import logging

from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.execution import Execution
from medperf.utils import generate_tmp_path, remove_path
import medperf.config as config
from medperf.exceptions import ExecutionError, CommunicationError, CleanExit
import yaml
from time import time


class ExecutionFlow:
    @classmethod
    def run(
        cls,
        dataset: Dataset,
        model: Cube,
        evaluator: Cube,
        execution: Execution = None,
        ignore_model_errors=False,
    ):
        """Benchmark execution flow.

        Args:
            benchmark_uid (int): UID of the desired benchmark
            data_uid (str): Registered Dataset UID
            model_uid (int): UID of model to execute
        """
        execution_flow = cls(dataset, model, evaluator, execution, ignore_model_errors)
        execution_flow.prepare()
        with execution_flow.ui.interactive():
            execution_flow.set_pending_status()
            execution_flow.run_inference()
            execution_flow.run_evaluation()
        execution_summary = execution_flow.todict()
        return execution_summary

    def __init__(
        self,
        dataset: Dataset,
        model: Cube,
        evaluator: Cube,
        execution: Execution = None,
        ignore_model_errors=False,
    ):
        self.comms = config.comms
        self.ui = config.ui
        self.dataset = dataset
        self.model = model
        self.evaluator = evaluator
        self.execution = execution
        self.ignore_model_errors = ignore_model_errors

    def prepare(self):
        self.partial = False
        self.preds_path = self.__setup_predictions_path()
        self.model_logs_path, self.metrics_logs_path = self.__setup_logs_path()
        self.results_path = generate_tmp_path()
        self.local_outputs_path = self.__setup_local_outputs_path()
        logging.debug(f"tmp results output: {self.results_path}")

    def __setup_logs_path(self):
        model_uid = self.model.local_id
        eval_uid = self.evaluator.local_id
        data_uid = self.dataset.local_id

        logs_path = os.path.join(
            config.experiments_logs_folder, str(model_uid), str(data_uid)
        )
        os.makedirs(logs_path, exist_ok=True)
        model_logs_path = os.path.join(logs_path, "model.log")
        metrics_logs_path = os.path.join(logs_path, f"metrics_{eval_uid}.log")
        return model_logs_path, metrics_logs_path

    def __setup_predictions_path(self):
        if self.execution is not None and self.execution.id is not None:
            timestamp = str(time()).replace(".", "_")
            preds_path = os.path.join(
                config.predictions_folder, str(self.execution.id), timestamp
            )
        else:
            # for compatibility test execution flows
            model_uid = self.model.local_id
            data_uid = self.dataset.local_id
            preds_path = os.path.join(
                config.predictions_folder, str(model_uid), str(data_uid)
            )
            remove_path(preds_path)  # clear it

        return preds_path

    def __setup_local_outputs_path(self):
        if self.execution is not None and self.execution.id is not None:
            local_outputs_path = self.execution.local_outputs_path
        else:
            # Non-persistent for compatibility test execution flows
            # TODO: make this better
            local_outputs_path = generate_tmp_path()

        return local_outputs_path

    def set_pending_status(self):
        self.__send_model_report("pending")
        self.__send_evaluator_report("pending")

    def run_inference(self):
        self.ui.text = f"Running inference of model '{self.model.name}' on dataset"
        infer_timeout = config.infer_timeout
        inference_mounts = {
            "data_path": self.dataset.data_path,
            "output_path": self.preds_path,
        }
        self.__send_model_report("started")
        try:
            self.model.run(
                task="infer",
                output_logs=self.model_logs_path,
                timeout=infer_timeout,
                mounts=inference_mounts,
            )
            self.ui.print("> Model execution complete")

        except ExecutionError as e:
            self.__send_model_report("failed")
            if not self.ignore_model_errors:
                logging.error(f"Model Execution failed: {e}")
                raise ExecutionError(f"Model Execution failed: {e}")
            else:
                self.partial = True
                logging.warning(f"Model Execution failed: {e}")
                return
        except KeyboardInterrupt:
            logging.warning("Model Execution interrupted by user")
            self.__send_model_report("interrupted")
            raise CleanExit("Model Execution interrupted by user")
        self.__send_model_report("finished")

    def run_evaluation(self):
        self.ui.text = f"Calculating metrics for model '{self.model.name}' predictions"
        evaluate_timeout = config.evaluate_timeout
        evaluator_mounts = {
            "predictions": self.preds_path,
            "labels": self.dataset.labels_path,
            "output_path": self.results_path,
            "local_outputs_path": self.local_outputs_path,
        }
        self.__send_evaluator_report("started")
        try:
            self.evaluator.run(
                task="evaluate",
                output_logs=self.metrics_logs_path,
                timeout=evaluate_timeout,
                mounts=evaluator_mounts,
            )
        except ExecutionError as e:
            logging.error(f"Metrics calculation failed: {e}")
            self.__send_evaluator_report("failed")
            raise ExecutionError(f"Metrics calculation failed: {e}")
        except KeyboardInterrupt:
            logging.warning("Metrics calculation interrupted by user")
            self.__send_evaluator_report("interrupted")
            raise CleanExit("Metrics calculation interrupted by user")
        self.__send_evaluator_report("finished")

    def todict(self):
        return {
            "results": self.get_results(),
            "partial": self.partial,
        }

    def get_results(self):
        if not os.path.exists(self.results_path):
            raise ExecutionError("Results file does not exist")
        with open(self.results_path, "r") as f:
            results = yaml.safe_load(f)
        if results is None:
            raise ExecutionError("Results file is empty")
        return results

    def __send_model_report(self, status: str):
        self.__send_report("model_report", status)

    def __send_evaluator_report(self, status: str):
        self.__send_report("evaluation_report", status)

    def __send_report(self, field: str, status: str):
        if self.execution is None or self.execution.id is None:
            return

        execution_id = self.execution.id
        body = {field: {"execution_status": status}}
        try:
            config.comms.update_execution(execution_id, body)
        except CommunicationError as e:
            logging.error(str(e))
            return
