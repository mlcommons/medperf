import os
import logging

from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.utils import (
    generate_tmp_path,
    storage_path,
    cleanup_path,
)
import medperf.config as config
from medperf.exceptions import ExecutionError
import yaml


class Execution:
    @classmethod
    def run(
        cls, dataset: Dataset, model: Cube, evaluator: Cube, ignore_errors=False,
    ):
        """Benchmark execution flow.

        Args:
            benchmark_uid (int): UID of the desired benchmark
            data_uid (str): Registered Dataset UID
            model_uid (int): UID of model to execute
        """
        execution = cls(dataset, model, evaluator, ignore_errors,)
        execution.prepare()
        with execution.ui.interactive():
            execution.run_inference()
            execution.run_evaluation()
        return execution.todict()

    def __init__(
        self, dataset: Dataset, model: Cube, evaluator: Cube, ignore_errors=False,
    ):

        self.comms = config.comms
        self.ui = config.ui
        self.dataset = dataset
        self.model = model
        self.evaluator = evaluator
        self.ignore_errors = ignore_errors

    def prepare(self):
        model_uid = self.model.uid
        data_uid = self.dataset.uid
        preds_path = os.path.join(
            config.predictions_storage, str(model_uid), str(data_uid)
        )

        self.partial = False
        self.out_path = generate_tmp_path()
        self.preds_path = storage_path(preds_path)

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
            if not self.ignore_errors:
                logging.error(f"Model MLCube Execution failed: {e}")
                cleanup_path(preds_path)
                raise ExecutionError("Model MLCube failed")
            else:
                self.partial = True
                logging.warning(f"Model MLCube Execution failed: {e}")

    def run_evaluation(self):
        self.ui.text = "Running model evaluation on dataset"
        evaluate_timeout = config.evaluate_timeout
        preds_path = self.preds_path
        labels_path = self.dataset.labels_path
        out_path = self.out_path
        try:
            self.ui.text = "Evaluating results"
            self.evaluator.run(
                task="evaluate",
                timeout=evaluate_timeout,
                predictions=preds_path,
                labels=labels_path,
                output_path=out_path,
                string_params={
                    "Ptasks.evaluate.parameters.input.predictions.opts": "ro",
                    "Ptasks.evaluate.parameters.input.labels.opts": "ro",
                },
            )
        except ExecutionError as e:
            logging.error(f"Metrics MLCube Execution failed: {e}")
            cleanup_path(preds_path)
            cleanup_path(out_path)
            raise ExecutionError("Metrics MLCube failed")

    def todict(self):
        return {
            "results": self.get_temp_results(),
            "partial": self.partial,
        }

    def get_temp_results(self):
        with open(self.out_path, "r") as f:
            results = yaml.safe_load(f)
        os.remove(self.out_path)
        return results
