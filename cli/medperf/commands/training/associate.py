from medperf import config
from medperf.entities.dataset import Dataset
from medperf.entities.training_exp import TrainingExp
from medperf.utils import approval_prompt, generate_data_csr
from medperf.exceptions import InvalidArgumentError


class DatasetTrainingAssociation:
    @staticmethod
    def run(training_exp_id: int, data_uid: int, approved=False):
        """Associates a registered dataset with a benchmark

        Args:
            data_uid (int): UID of the registered dataset to associate
            benchmark_uid (int): UID of the benchmark to associate with
        """
        comms = config.comms
        ui = config.ui
        dset = Dataset.get(data_uid)
        if dset.id is None:
            msg = "The provided dataset is not registered."
            raise InvalidArgumentError(msg)

        training_exp = TrainingExp.get(training_exp_id)

        if dset.data_preparation_mlcube != training_exp.data_preparation_mlcube:
            raise InvalidArgumentError(
                "The specified dataset wasn't prepared for this benchmark"
            )

        email = ""  # TODO
        csr, csr_hash = generate_data_csr(email, data_uid, training_exp_id)
        msg = "Please confirm that you would like to associate"
        msg += f" the dataset {dset.name} with the training exp {training_exp.name}."
        msg += f" The certificate signing request hash is: {csr_hash}"
        msg += " [Y/n]"

        approved = approved or approval_prompt(msg)
        if approved:
            ui.print("Generating dataset training association")
            # TODO: delete keys if upload fails
            #       check if on failure, other (possible) request will overwrite key
            comms.associate_training_dset(dset.id, training_exp_id, csr)
        else:
            ui.print("Dataset association operation cancelled.")
