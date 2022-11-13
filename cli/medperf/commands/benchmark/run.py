import medperf.config as config
from medperf.commands.result.create import BenchmarkExecution
from medperf.entities.benchmark import Benchmark
from medperf.entities.result import Result
from tabulate import tabulate


class BenchmarkRunAll:
    @classmethod
    def run(
        cls, benchmark_uid: str, data_uid: str, ignore_errors=False,
    ):
        """Submits a new cube to the medperf platform
        Args:
            benchmark_uid:
            data_uid: generated uid
        """
        execution = cls(benchmark_uid, data_uid, ignore_errors)
        execution.get_models()
        execution.filter_models()
        execution.run_models()
        execution.print_summary()

    def __init__(self, benchmark_uid: str, data_uid: str, ignore_errors=False):
        self.comms = config.comms
        self.ui = config.ui
        self.benchmark_uid = benchmark_uid
        self.data_uid = data_uid
        self.ignore_errors = ignore_errors
        self.summary = {}

    def get_models(self):
        self.models = Benchmark.get_models_uids(self.benchmark_uid)
        self.summary["num_models"] = len(self.models)

    def filter_models(self):
        # TODO: this should contain all (server+local)
        results = Result.all()
        results = [
            result
            for result in results
            if result.benchmark_uid == self.benchmark_uid
            and result.dataset_uid == self.data_uid
        ]
        done_models = [result.model_uid for result in results]
        self.models = [model for model in self.models if model not in done_models]
        self.summary["skipped_models"] = len(done_models)

    def run_models(self):
        self.summary["executions"] = []
        if len(self.models) == 0:
            return
        execution = BenchmarkExecution(
            self.benchmark_uid,
            self.data_uid,
            self.models[0],
            ignore_errors=self.ignore_errors,
        )
        execution.prepare()
        try:
            execution.validate()
        except SystemExit:
            # We are sure that if this happens then it is
            # because of an invalid data uid
            return
        execution.evaluator = execution.__get_cube(
            execution.benchmark.evaluator, "Evaluator"
        )
        for model in self.models:
            exec_summary = {
                "model": model,
                "success": False,
                "partial": "",
                "error": "",
            }

            try:
                execution.model_uid = model
                execution.model_cube = execution.__get_cube(model, "Model")
                execution.run_cubes()
            except Exception as e:
                self.ui.print_error(
                    f"Cannot execute the benchmark with the model {model}: {e}"
                )
                exec_summary["error"] = str(e)
                self.summary["executions"].append(exec_summary)
                continue

            except SystemExit:  # TODO: to think what to do!
                self.ui.print_error(f"Benchmark execution failed for model {model}")
                exec_summary["error"] = "MLCube failure"
                self.summary["executions"].append(exec_summary)
                continue

            # If an error is raised during the two commands below, it is not model-specific
            execution.write()
            execution.remove_temp_results()

            exec_summary["success"] = True
            exec_summary["partial"] = execution.metadata["partial"]
            self.summary["executions"].append(exec_summary)

    def print_summary(self):
        executions = self.summary["executions"]

        num_total = self.summary["num_models"]
        num_skipped = self.summary["skipped_models"]
        num_success = sum([exec_summary["success"] for exec_summary in executions])
        num_failed = num_total - num_skipped - num_success
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

        self.ui.print(tab)
        self.ui.print(msg)
