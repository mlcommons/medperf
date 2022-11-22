from medperf import config
from medperf.utils import pretty_error


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
        priority_setter.prevent_underflow()  # TODO: should be after update!?
        priority_setter.update()

    def __init__(self, benchmark_uid: str, mlcube_uid: str, priority: int):
        self.benchmark_uid = benchmark_uid
        self.mlcube_uid = mlcube_uid
        self.priority = priority
        self.float_priority = None
        self.min_difference = None
        self.comms = config.comms

    def validate(self):
        if self.priority < 1 and self.priority != -1:
            pretty_error(
                "Invalid arguments. Priority value must be a positive integer or (-1) for least priority"
            )

    def convert_priority_to_float(self):
        """Converts an integer-valued priority into a float value.
        Priority values in the server are stored as float values (not integer ranks) for more efficient
        priority updates in terms of database operations. More information can be found here:
        https://questhenkart.medium.com/a-scalable-solution-to-ordering-data-by-priority-or-rank-19977d31817c

        Args:
            benchmark_uid (str): Benchmark UID of the mlcube association whose priority is given.
            priority (int): priority value (rank). A positive integer or (-1) for least priority"

        Returns:
            float: the float value that corresponds to the given priority.
        """

        bmk_models = config.comms.get_benchmark_model_associations(self.benchmark_uid)
        priorities = [bmk_model["priority"] for bmk_model in bmk_models]

        if self.priority == -1 or self.priority >= len(priorities):
            self.float_priority = priorities[-1] + 1.0
        elif self.priority == 1:
            self.float_priority = priorities[0] - 1.0
        else:
            priority1 = priorities[self.priority - 1]
            priority2 = priorities[self.priority - 2]
            self.float_priority = (priority1 + priority2) / 2
            self.min_difference = (priority2 - priority1) / 2

    def prevent_underflow(self):
        # this number is chosen arbitrarily
        if self.min_difference > 1e-10:
            return
        # TODO
        # for i, bmk_model in enumerate(bmk_models):
        #     bmk_model.priority = i + 1.0
        # BenchmarkModel.objects.bulk_update(bmk_models, ["priority"])

    def update(self):
        self.comms.set_mlcube_association_priority(
            self.benchmark_uid, self.mlcube_uid, self.float_priority
        )
