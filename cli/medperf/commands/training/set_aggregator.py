from medperf import config
from medperf.entities.aggregator import Aggregator
from medperf.entities.training_exp import TrainingExp
from medperf.utils import approval_prompt
from medperf.exceptions import CleanExit, InvalidArgumentError


class SetAggregator:
    @classmethod
    def run(cls, training_exp_id: int, aggregator_id: int, approved: bool = False):
        """Sets the aggregator for a training experiment.

        Args:
            training_exp_id (int): UID of the training experiment
            aggregator_id (int): UID of the registered aggregator to set
            approved (bool): If True, skip confirmation prompt
        """
        ui = config.ui

        submission = cls(training_exp_id, aggregator_id, approved)
        with ui.interactive():
            submission.validate()
            submission.prepare()
            submission.submit()

    def __init__(self, training_exp_id: int, aggregator_id: int, approval: bool):
        self.ui = config.ui
        self.comms = config.comms
        self.training_exp_id = training_exp_id
        self.aggregator_id = aggregator_id
        self.approved = approval

    def validate(self):
        if self.aggregator_id is None:
            raise InvalidArgumentError("An aggregator ID must be provided")
        if self.training_exp_id is None:
            raise InvalidArgumentError("A training experiment ID must be provided")

    def prepare(self):
        self.training_exp = TrainingExp.get(self.training_exp_id)
        self.aggregator = Aggregator.get(self.aggregator_id)

    def submit(self):
        training_exp_name = self.training_exp.name
        self.ui.text = (
            f"Setting aggregator for training experiment '{training_exp_name}'"
        )
        body = {"aggregator": self.aggregator_id}
        msg = (
            f"You are about to set the aggregator {self.aggregator.name} for training experiment {training_exp_name}."
            " Do you confirm? [Y/n] "
        )
        self.approved = self.approved or approval_prompt(msg)

        if self.approved:
            self.comms.set_training_exp_aggregator(self.training_exp_id, body)
            return
        raise CleanExit("Aggregator setting cancelled")
