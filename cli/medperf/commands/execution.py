import os
import logging

from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.utils import cleanup_path, generate_tmp_path, storage_path
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
        execution.store_predictions()
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
        self.preds_path = generate_tmp_path()
        self.results_path = generate_tmp_path()
        logging.debug(f"tmp predictions output: {self.preds_path}")
        logging.debug(f"tmp results output: {self.results_path}")

    def run_inference(self):
        self.ui.text = "Running model inference on dataset"
        infer_timeout = config.infer_timeout
        preds_path = self.preds_path
        data_path = self.dataset.data_path
        try:
            self.model.run(
                task="infer",
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
        self.evaluator.run(
            task="evaluate",
            timeout=evaluate_timeout,
            predictions=preds_path,
            labels=labels_path,
            output_path=results_path,
            string_params={
                "Ptasks.evaluate.parameters.input.predictions.opts": "ro",
                "Ptasks.evaluate.parameters.input.labels.opts": "ro",
            },
        )

    def todict(self):
        return {
            "results": self.get_results(),
            "partial": self.partial,
        }

    def get_results(self):
        with open(self.results_path, "r") as f:
            results = yaml.safe_load(f)
        return results

    def store_predictions(self):
        model_uid = self.model.generated_uid
        data_hash = self.dataset.generated_uid
        new_preds_path = os.path.join(
            config.predictions_storage, str(model_uid), str(data_hash)
        )
        new_preds_path = storage_path(new_preds_path)
        cleanup_path(new_preds_path)
        # NOTE: currently prediction are overwritten if found.
        # when we start caring about storing predictions for use after
        # result creation, we should change this
        os.makedirs(new_preds_path)
        os.rename(self.preds_path, new_preds_path)
