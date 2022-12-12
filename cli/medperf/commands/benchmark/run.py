import medperf.config as config
from medperf.commands.result.create import BenchmarkExecution
from medperf.entities.result import Result
from medperf.exceptions import ExecutionError, InvalidEntityError
from medperf.utils import results_path
from tabulate import tabulate


class BenchmarkRunAll:
    @classmethod
    def run(
        cls, benchmark_uid: str, data_uid: str, ignore_errors=False,
    ):
        """Runs all outstanding models of a benchmark
        Args:
            benchmark_uid:
            data_uid: data uid
        """
        execution = cls(benchmark_uid, data_uid, ignore_errors)
        execution.prepare()
        execution.validate()
        execution.prepare_cubes()
        execution.run_models()
        execution.print_summary()

    def __init__(self, benchmark_uid: str, data_uid: str, ignore_errors=False):
        self.benchmark_uid = benchmark_uid
        self.data_uid = data_uid
        self.model_execution = BenchmarkExecution(
            benchmark_uid, data_uid, None, ignore_errors=ignore_errors,
        )
        self.outstanding_models = []
        self.summary = {}

    def prepare(self):
        self.model_execution.prepare()
        self.model_execution.model_uid = self.model_execution.benchmark.models[0]

    def validate(self):
        self.model_execution.validate()

    def prepare_cubes(self):
        self.model_execution.evaluator = self.model_execution.__get_cube(
            self.model_execution.benchmark.evaluator, "Evaluator"
        )
        self.__filter_models()

    def __filter_models(self):
        benchmark_models = self.model_execution.benchmark.models
        results = Result.all()
        results = [
            result
            for result in results
            if result.benchmark_uid == self.benchmark_uid
            and result.dataset_uid == self.data_uid
        ]
        done_models = [result.model_uid for result in results]
        self.outstanding_models = [
            model for model in benchmark_models if model not in done_models
        ]
        self.summary["skipped_models"] = len(done_models)

    def run_models(self):
        self.summary["executions"] = []
        for model in self.outstanding_models:
            exec_summary = {
                "model": model,
                "success": False,
                "partial": "",
                "error": "",
            }
            # reset
            self.model_execution.model_uid = model
            self.model_execution.out_path = results_path(
                self.benchmark_uid, model, self.model_execution.dataset.uid
            )
            self.model_execution.metadata["partial"] = False

            try:
                self.model_execution.model_cube = self.model_execution.__get_cube(
                    model, "Model"
                )
            except InvalidEntityError as e:
                config.ui.print_error(
                    f"There was an error when retrieving the model mlcube {model}: {e}"
                )
                exec_summary["error"] = str(e)
                self.summary["executions"].append(exec_summary)
                continue
            try:
                self.model_execution.run_cubes()
            except ExecutionError as e:
                config.ui.print_error(
                    f"There was an error when executing the benchmark with the model {model}: {e}"
                )
                exec_summary["error"] = str(e)
                self.summary["executions"].append(exec_summary)
                continue

            self.model_execution.write()
            self.model_execution.remove_temp_results()

            exec_summary["success"] = True
            exec_summary["partial"] = self.model_execution.metadata["partial"]
            self.summary["executions"].append(exec_summary)

    def print_summary(self):
        executions = self.summary["executions"]

        num_success = sum([exec_summary["success"] for exec_summary in executions])
        num_failed = len(executions) - num_success
        num_skipped = self.summary["skipped_models"]
        num_total = num_success + num_failed + num_skipped

        num_partial = sum(
            [exec_summary["partial"] is True for exec_summary in executions]
        )

        headers = ["model", "success", "partial", "error"]
        data = [[exec_summary[key] for key in headers] for exec_summary in executions]
        tab = tabulate(data, headers=headers)

        msg = f"Total benchmark models: {num_total}\n"
        msg += f"\t{num_skipped} were skipped (already executed)\n"
        msg += f"\t{num_failed} failed\n"
        msg += f"\t{num_success} ran successfully, with {num_partial} partial results\n"

        config.ui.print(tab)
        config.ui.print(msg)
