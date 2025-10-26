import os
from medperf import config
from medperf.entities.ca import CA
from medperf.entities.event import TrainingEvent
from medperf.exceptions import InvalidArgumentError, MedperfException
from medperf.entities.training_exp import TrainingExp
from medperf.entities.aggregator import Aggregator
from medperf.entities.cube import Cube
from medperf.utils import get_pki_assets_path, remove_path
from medperf.certificates import trust


class StartAggregator:
    @classmethod
    def run(
        cls,
        training_exp_id: int,
        publish_on: str = "127.0.0.1",
        overwrite: bool = False,
    ):
        """Starts the aggregation server of a training experiment

        Args:
            training_exp_id (int): Training experiment UID.
        """
        execution = cls(training_exp_id, publish_on, overwrite)
        execution.prepare()
        execution.validate()
        execution.check_existing_outputs()
        execution.prepare_aggregator()
        execution.prepare_participants_list()
        execution.prepare_plan()
        execution.prepare_pki_assets()
        with config.ui.interactive():
            execution.run_experiment()

    def __init__(self, training_exp_id, publish_on, overwrite) -> None:
        self.training_exp_id = training_exp_id
        self.overwrite = overwrite
        self.publish_on = publish_on
        self.ui = config.ui

    def prepare(self):
        self.training_exp = TrainingExp.get(self.training_exp_id)
        self.ui.print(f"Training Execution: {self.training_exp.name}")
        self.event = TrainingEvent.from_experiment(self.training_exp_id)

    def validate(self):
        if self.event.finished:
            msg = "The provided training experiment has to start a training event."
            raise InvalidArgumentError(msg)

    def check_existing_outputs(self):
        msg = (
            "Outputs still exist from previous runs. Overwrite"
            " them by rerunning the command with --overwrite"
        )
        paths = [
            self.event.agg_out_logs,
            self.event.out_weights,
            self.event.report_path,
        ]
        for path in paths:
            if os.path.exists(path):
                if not self.overwrite:
                    raise MedperfException(msg)
                remove_path(path)

    def prepare_aggregator(self):
        self.aggregator = Aggregator.from_experiment(self.training_exp_id)
        self.cube = self.__get_cube(self.aggregator.aggregation_mlcube, "aggregation")

    def __get_cube(self, uid: int, name: str) -> Cube:
        self.ui.text = f"Retrieving container '{name}'"
        cube = Cube.get(uid)
        cube.download_run_files()
        self.ui.print(f"> container '{name}' download complete")
        return cube

    def prepare_participants_list(self):
        self.event.prepare_participants_list()

    def prepare_plan(self):
        self.training_exp.prepare_plan()

    def prepare_pki_assets(self):
        ca = CA.from_experiment(self.training_exp_id)
        trust(ca)
        agg_address = self.aggregator.address
        self.aggregator_pki_assets = get_pki_assets_path(agg_address, ca.id)
        self.ca = ca

    def run_experiment(self):
        mounts = {
            "node_cert_folder": self.aggregator_pki_assets,
            "ca_cert_folder": self.ca.pki_assets,
            "plan_path": self.training_exp.plan_path,
            "collaborators": self.event.participants_list_path,
            "output_logs": self.event.agg_out_logs,
            "output_weights": self.event.out_weights,
            "report_path": self.event.report_path,
        }

        self.ui.text = "Running Aggregator"
        port = self.aggregator.port
        self.cube.run(
            task="start_aggregator",
            mounts=mounts,
            ports=[f"{self.publish_on}:{port}:{port}"],
            disable_network=False,
        )
