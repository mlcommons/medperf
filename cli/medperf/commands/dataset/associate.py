from medperf.commands.dataset.associate_benchmark import AssociateBenchmarkDataset
from medperf.commands.dataset.associate_training import AssociateTrainingDataset
from medperf.exceptions import InvalidArgumentError


class AssociateDataset:
    @staticmethod
    def run(
        data_uid: int,
        benchmark_uid: int = None,
        training_exp_uid: int = None,
        approved=False,
        no_cache=False,
    ):
        """Associates a dataset with a benchmark or a training exp"""
        too_many_resources = benchmark_uid and training_exp_uid
        no_resource = benchmark_uid is None and training_exp_uid is None
        if no_resource or too_many_resources:
            raise InvalidArgumentError(
                "Must provide either a benchmark or a training experiment"
            )
        if benchmark_uid:
            AssociateBenchmarkDataset.run(
                data_uid, benchmark_uid, approved=approved, no_cache=no_cache
            )
        if training_exp_uid:
            if no_cache:
                raise InvalidArgumentError(
                    "no_cache argument is only valid when associating with a benchmark"
                )
            AssociateTrainingDataset.run(data_uid, training_exp_uid, approved=approved)
