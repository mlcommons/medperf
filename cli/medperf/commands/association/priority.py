from medperf import config
from medperf.exceptions import InvalidArgumentError
from medperf.entities.benchmark import Benchmark


class AssociationPriority:
    @staticmethod
    def run(benchmark_uid: int, model_uid: int, priority: int):
        """Sets priority for an association between a benchmark and a model

        Args:
            benchmark_uid (int): Benchmark UID.
            model_uid (int): Model UID.
            priority (int): priority value

        """
        associated_models = Benchmark.get_models_uids(benchmark_uid)
        if model_uid not in associated_models:
            raise InvalidArgumentError(
                "The given model doesn't exist or is not associated with the benchmark"
            )
        config.comms.update_benchmark_model_association(
            benchmark_uid, model_uid, {"priority": priority}
        )
