from medperf import config
from medperf.entities.ca import CA
from medperf.entities.training_exp import TrainingExp
from medperf.utils import approval_prompt
from medperf.exceptions import InvalidArgumentError


class AssociateCA:
    @staticmethod
    def run(training_exp_id: int, ca_uid: int, approved=False):
        """Associates an ca with a training experiment

        Args:
            ca_uid (int): UID of the registered ca to associate
            benchmark_uid (int): UID of the benchmark to associate with
        """
        comms = config.comms
        ui = config.ui
        ca = CA.get(ca_uid)
        if ca.id is None:
            msg = "The provided ca is not registered."
            raise InvalidArgumentError(msg)

        training_exp = TrainingExp.get(training_exp_id)
        msg = "Please confirm that you would like to associate"
        msg += f" the ca {ca.name} with the training exp {training_exp.name}."
        msg += " [Y/n]"

        approved = approved or approval_prompt(msg)
        if approved:
            ui.print("Generating ca training association")
            comms.associate_training_ca(ca.id, training_exp_id)
        else:
            ui.print("CA association operation cancelled.")
