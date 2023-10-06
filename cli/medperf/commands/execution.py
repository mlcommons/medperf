import os
import logging

from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.utils import generate_tmp_path, storage_path
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
        model_uid = self.model.generated_uid
        eval_uid = self.evaluator.generated_uid
        data_hash = self.dataset.generated_uid

        logs_path = os.path.join(
            config.experiments_logs_storage, str(model_uid), str(data_hash)
        )
        logs_path = storage_path(logs_path)
        os.makedirs(logs_path, exist_ok=True)
        model_logs_path = os.path.join(logs_path, "model.log")
        metrics_logs_path = os.path.join(logs_path, f"metrics_{eval_uid}.log")
        return model_logs_path, metrics_logs_path

    def __setup_predictions_path(self):
        model_uid = self.model.generated_uid
        data_hash = self.dataset.generated_uid
        preds_path = os.path.join(
            config.predictions_storage, str(model_uid), str(data_hash)
        )
        preds_path = storage_path(preds_path)
        if os.path.exists(preds_path):
            msg = f"Found existing predictions for model {self.model.id} on dataset "
            msg += f"{self.dataset.id} at {preds_path}. Consider deleting this "
            msg += "folder if you wish to overwrite the predictions."
            raise ExecutionError(msg)
        return preds_path

    def run_inference(self):
        self.ui.text = "Running model inference on dataset"
        infer_timeout = config.infer_timeout
        preds_path = self.preds_path
        data_path = self.dataset.data_path
        try:
            self.model.run(
                task="infer",
                output_logs=self.model_logs_path,
                timeout=infer_timeout,
                data_path=data_path,
                output_path=preds_path,
                string_params={"Ptasks.infer.parameters.input.data_path.opts": "ro"},
            )
            self.ui.print("> Model execution complete")

        except ExecutionError as e:
            if not self.ignore_model_errors:
                logging.error(f"Model MLCube Execution failed: {e}")
                raise ExecutionError("Model MLCube failed")
            else:
                self.partial = True
                logging.warning(f"Model MLCube Execution failed: {e}")

    def run_evaluation(self):
        self.ui.text = "Running model evaluation on dataset"
        evaluate_timeout = config.evaluate_timeout
        preds_path = self.preds_path
        labels_path = self.dataset.labels_path
        results_path = self.results_path
        self.ui.text = "Evaluating results"
        try:
            self.evaluator.run(
                task="evaluate",
                output_logs=self.metrics_logs_path,
                timeout=evaluate_timeout,
                predictions=preds_path,
                labels=labels_path,
                output_path=results_path,
                string_params={
                    "Ptasks.evaluate.parameters.input.predictions.opts": "ro",
                    "Ptasks.evaluate.parameters.input.labels.opts": "ro",
                },
            )
        except ExecutionError as e:
            logging.error(f"Metrics MLCube Execution failed: {e}")
            raise ExecutionError("Metrics MLCube failed")

    def todict(self):
        return {
            "results": self.get_results(),
            "partial": self.partial,
        }

    def get_results(self):
        with open(self.results_path, "r") as f:
            results = yaml.safe_load(f)
        return results
