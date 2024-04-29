from medperf import config
from medperf.entities.aggregator import Aggregator
from medperf.entities.training_exp import TrainingExp
from medperf.utils import approval_prompt
from medperf.exceptions import InvalidArgumentError


class AssociateAggregator:
    @staticmethod
    def run(training_exp_id: int, agg_uid: int, approved=False):
        """Associates an aggregator with a training experiment

        Args:
            agg_uid (int): UID of the registered aggregator to associate
            benchmark_uid (int): UID of the benchmark to associate with
        """
        comms = config.comms
        ui = config.ui
        agg = Aggregator.get(agg_uid)
        if agg.id is None:
            msg = "The provided aggregator is not registered."
            raise InvalidArgumentError(msg)

        training_exp = TrainingExp.get(training_exp_id)
        msg = "Please confirm that you would like to associate"
        msg += f" the aggregator {agg.name} with the training exp {training_exp.name}."
        msg += " [Y/n]"

        approved = approved or approval_prompt(msg)
        if approved:
            ui.print("Generating aggregator training association")
            comms.associate_training_aggregator(agg.id, training_exp_id)
        else:
            ui.print("Aggregator association operation cancelled.")
