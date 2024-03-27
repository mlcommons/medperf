from medperf import config
from medperf.entities.aggregator import Aggregator
from medperf.entities.training_exp import TrainingExp
from medperf.utils import approval_prompt, generate_agg_csr
from medperf.exceptions import InvalidArgumentError


class AssociateAggregator:
    @staticmethod
    def run(training_exp_id: int, agg_uid: int, approved=False):
        """Associates a registered aggregator with a benchmark

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
        csr, csr_hash = generate_agg_csr(training_exp_id, agg.address, agg.id)
        msg = "Please confirm that you would like to associate"
        msg += f" the aggregator {agg.name} with the training exp {training_exp.name}."
        msg += f" The certificate signing request hash is: {csr_hash}"
        msg += " [Y/n]"

        approved = approved or approval_prompt(msg)
        if approved:
            ui.print("Generating aggregator training association")
            # TODO: delete keys if upload fails
            #       check if on failure, other (possible) request will overwrite key
            comms.associate_aggregator(agg.id, training_exp_id, csr)
        else:
            ui.print("Aggregator association operation cancelled.")
