from medperf import config
from medperf.entities.training_exp import TrainingExp


class LockTrainingExp:
    @staticmethod
    def run(training_exp_id: int):
        """Sets approval status for an association between a benchmark and a dataset or mlcube

        Args:
            benchmark_uid (int): Benchmark UID.
            approval_status (str): Desired approval status to set for the association.
            comms (Comms): Instance of Comms interface.
            ui (UI): Instance of UI interface.
            dataset_uid (int, optional): Dataset UID. Defaults to None.
            mlcube_uid (int, optional): MLCube UID. Defaults to None.
        """
        # TODO: this logic will be refactored when we merge entity edit PR
        comms = config.comms
        comms.set_experiment_as_operational(training_exp_id)
        # update training experiment
        training_exp = TrainingExp.get(training_exp_id)
        training_exp.write()
