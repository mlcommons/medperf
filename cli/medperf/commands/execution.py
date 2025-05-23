import os
import logging

from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.utils import generate_tmp_path
import medperf.config as config
from medperf.exceptions import ExecutionError
import yaml


class Execution:
    @classmethod
    def run(
        cls, dataset: Dataset, model: Cube, evaluator: Cube, ignore_model_errors=False
    ):
        """Benchmark execution flow.

        Args:
            benchmark_uid (int): UID of the desired benchmark
            data_uid (str): Registered Dataset UID
            model_uid (int): UID of model to execute
        """
        execution = cls(dataset, model, evaluator, ignore_model_errors)
        execution.prepare()
        with execution.ui.interactive():
            execution.run_inference()
            execution.run_evaluation()
        execution_summary = execution.todict()
        return execution_summary

    def __init__(
        self, dataset: Dataset, model: Cube, evaluator: Cube, ignore_model_errors=False
    ):
        self.comms = config.comms
        self.ui = config.ui
        self.dataset = dataset
        self.model = model
        self.evaluator = evaluator
        self.ignore_model_errors = ignore_model_errors

    def prepare(self):
        self.partial = False
        self.preds_path = self.__setup_predictions_path()
        self.model_logs_path, self.metrics_logs_path = self.__setup_logs_path()
        self.results_path = generate_tmp_path()
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
        model_uid = self.model.local_id
        data_uid = self.dataset.local_id
        preds_path = os.path.join(
            config.predictions_folder, str(model_uid), str(data_uid)
        )
        if os.path.exists(preds_path):
            msg = f"Found existing predictions for model {self.model.id} on dataset "
            msg += f"{self.dataset.id} at {preds_path}. Consider deleting this "
            msg += "folder if you wish to overwrite the predictions."
            raise ExecutionError(msg)
        return preds_path

    def run_inference(self):
        self.ui.text = "Running model inference on dataset"
        infer_timeout = config.infer_timeout
        inference_mounts = {
            "data_path": self.dataset.data_path,
            "output_path": self.preds_path,
        }
        try:
            self.model.run(
                task="infer",
                output_logs=self.model_logs_path,
                timeout=infer_timeout,
                mounts=inference_mounts,
            )
            self.ui.print("> Model execution complete")

        except ExecutionError as e:
            if not self.ignore_model_errors:
                logging.error(f"Model Execution failed: {e}")
                raise ExecutionError(f"Model failed: {e}")
            else:
                self.partial = True
                logging.warning(f"Model Execution failed: {e}")

    def run_evaluation(self):
        self.ui.text = "Running model evaluation on dataset"
        evaluate_timeout = config.evaluate_timeout
        evaluator_mounts = {
            "predictions": self.preds_path,
            "labels": self.dataset.labels_path,
            "output_path": self.results_path,
        }
        self.ui.text = "Evaluating results"
        try:
            self.evaluator.run(
                task="evaluate",
                output_logs=self.metrics_logs_path,
                timeout=evaluate_timeout,
                mounts=evaluator_mounts,
            )
        except ExecutionError as e:
            logging.error(f"Metrics Execution failed: {e}")
            raise ExecutionError("Metrics calculation failed")

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
