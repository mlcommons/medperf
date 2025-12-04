from medperf import config
from medperf.entities.dataset import Dataset
from medperf.entities.training_exp import TrainingExp
from medperf.utils import approval_prompt
from medperf.exceptions import InvalidArgumentError


class AssociateTrainingDataset:
    @staticmethod
    def run(data_uid: int, training_exp_uid: int, approved=False):
        """Associates a dataset with a training experiment

        Args:
            data_uid (int): UID of the registered dataset to associate
            training_exp_uid (int): UID of the training experiment to associate with
        """
        comms = config.comms
        ui = config.ui
        dset: Dataset = Dataset.get(data_uid)
        if dset.id is None:
            msg = "The provided dataset is not registered."
            raise InvalidArgumentError(msg)

        training_exp = TrainingExp.get(training_exp_uid)

        if dset.data_preparation_mlcube != training_exp.data_preparation_mlcube:
            raise InvalidArgumentError(
                "The specified dataset wasn't prepared for this experiment"
            )

        msg = "Please confirm that you would like to associate"
        msg += f" the dataset {dset.name} with the training experiment {training_exp.name}."
        msg += " [Y/n]"
        approved = approved or approval_prompt(msg)
        if approved:
            ui.print("Generating dataset training experiment association")
            comms.associate_training_dataset(dset.id, training_exp_uid)
        else:
            ui.print("Dataset association operation cancelled.")
