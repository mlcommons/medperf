from medperf import config
from medperf.exceptions import InvalidArgumentError
from medperf.entities.benchmark import Benchmark


class AssociationPriority:
    @staticmethod
    def run(benchmark_uid: int, mlcube_uid: int, priority: int):
        """Sets priority for an association between a benchmark and an mlcube

        Args:
            benchmark_uid (int): Benchmark UID.
            mlcube_uid (int): MLCube UID.
            priority (int): priority value

        """
        associated_cubes = Benchmark.get_models_uids(benchmark_uid)
        if mlcube_uid not in associated_cubes:
            raise InvalidArgumentError(
                "The given container doesn't exist or is not associated with the benchmark"
            )
        config.comms.update_benchmark_model_association(
            benchmark_uid, mlcube_uid, {"priority": priority}
        )
