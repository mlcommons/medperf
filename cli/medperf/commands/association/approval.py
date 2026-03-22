from medperf import config
from medperf.commands.association.utils import validate_args


class Approval:
    @staticmethod
    def run(
        approval_status: str,
        benchmark_uid: int = None,
        training_exp_uid: int = None,
        dataset_uid: int = None,
        model_uid: int = None,
    ):
        """Sets approval status for an association between a benchmark and a dataset or mlcube,
        or between a training experiment and a dataset.

        Args:
            benchmark_uid (int): Benchmark UID.
            approval_status (str): Desired approval status to set for the association.
            training_exp_uid (int, optional): Training experiment UID. Defaults to None.
            dataset_uid (int, optional): Dataset UID. Defaults to None.
            mlcube_uid (int, optional): MLCube UID. Defaults to None.
        """
        comms = config.comms
        validate_args(
            benchmark_uid,
            training_exp_uid,
            dataset_uid,
            model_uid,
            approval_status.value,
        )
        update = {"approval_status": approval_status.value}
        if benchmark_uid:
            if dataset_uid:
                comms.update_benchmark_dataset_association(
                    benchmark_uid, dataset_uid, update
                )

            if model_uid:
                comms.update_benchmark_model_association(
                    benchmark_uid, model_uid, update
                )
        if training_exp_uid and dataset_uid:
            comms.update_training_dataset_association(
                training_exp_uid, dataset_uid, update
            )
