from medperf import config
from medperf.exceptions import InvalidArgumentError


class Approval:
    @staticmethod
    def run(
        benchmark_uid: int,
        approval_status: str,
        dataset_uid: int = None,
        mlcube_uid: int = None,
    ):
        """Sets approval status for an association between a benchmark and a dataset or mlcube

        Args:
            benchmark_uid (int): Benchmark UID.
            approval_status (str): Desired approval status to set for the association.
            comms (Comms): Instance of Comms interface.
            ui (UI): Instance of UI interface.
            dataset_uid (int, optional): Dataset UID. Defaults to None.
            mlcube_uid (int, optional): MLCube UID. Defaults to None.
        """
        comms = config.comms
        too_many_resources = dataset_uid and mlcube_uid
        no_resource = dataset_uid is None and mlcube_uid is None
        if no_resource or too_many_resources:
            raise InvalidArgumentError("Must provide either a dataset or mlcube")

        if dataset_uid:
            comms.set_dataset_association_approval(
                benchmark_uid, dataset_uid, approval_status.value
            )

        if mlcube_uid:
            comms.set_mlcube_association_approval(
                benchmark_uid, mlcube_uid, approval_status.value
            )
