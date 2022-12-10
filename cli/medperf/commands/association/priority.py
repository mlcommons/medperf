from medperf import config
from medperf.exceptions import CleanExit, InvalidArgumentError


class AssociationPriority:
    @staticmethod
    def run(
        benchmark_uid: str, mlcube_uid: str, priority: int,
    ):
        """Sets priority for an association between a benchmark and an mlcube

        Args:
            benchmark_uid (str): Benchmark UID.
            mlcube_uid (str): MLCube UID.
            priority (int): priority value (rank). A positive integer or (-1) for least priority"

        """

        priority_setter = AssociationPriority(benchmark_uid, mlcube_uid, priority)
        priority_setter.validate()
        priority_setter.convert_priority_to_float()
        priority_setter.update()

    def __init__(self, benchmark_uid: str, mlcube_uid: str, priority: int):
        self.benchmark_uid = benchmark_uid
        self.mlcube_uid = mlcube_uid
        self.priority = priority
        self.float_priority = None
        self.min_difference = None
        self.priorities = []

    def validate(self):
        if self.priority < 1 and self.priority != -1:
            raise InvalidArgumentError(
                "Priority value must be a positive integer or (-1) for least priority"
            )

        self.assocs = config.comms.get_benchmark_model_associations(self.benchmark_uid)
        associated_cubes = [str(assoc["model_mlcube"]) for assoc in self.assocs]
        if self.mlcube_uid not in associated_cubes:
            raise InvalidArgumentError(
                "The given mlcube is not associated with the benchmark"
            )

        cube_priority = associated_cubes.index(self.mlcube_uid) + 1
        redundant_command = any(
            [
                cube_priority == len(self.assocs) and self.priority >= cube_priority,
                cube_priority == len(self.assocs) and self.priority == -1,
                cube_priority == self.priority,
            ]
        )
        if redundant_command:
            # TODO: raise SafeExit
            raise CleanExit("The given mlcube already has the specified priority")

    def convert_priority_to_float(self):
        """Converts an integer-valued priority into a float value. Keeps track of the minimalfloat precision
        reached
        Priority values in the server are stored as float values (not integer ranks) for more efficient
        priority updates in terms of database operations. More information can be found here:
        https://questhenkart.medium.com/a-scalable-solution-to-ordering-data-by-priority-or-rank-19977d31817c
        """

        priorities = [assoc["priority"] for assoc in self.assocs]

        if self.priority == -1 or self.priority >= len(priorities):
            self.float_priority = priorities[-1] + 1.0
        elif self.priority == 1:
            self.float_priority = priorities[0] - 1.0
        else:
            priority1 = priorities[self.priority - 1]
            priority2 = priorities[self.priority - 2]
            self.float_priority = (priority1 + priority2) / 2
            self.min_difference = (priority2 - priority1) / 2

    def update(self):
        rescale = (
            self.min_difference is not None
            and self.min_difference < config.priority_min_precision
        )
        config.comms.set_mlcube_association_priority(
            self.benchmark_uid, self.mlcube_uid, self.float_priority, rescale=rescale,
        )
