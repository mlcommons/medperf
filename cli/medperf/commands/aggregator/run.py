import os
from medperf import config
from medperf.exceptions import InvalidArgumentError
from medperf.entities.training_exp import TrainingExp
from medperf.entities.aggregator import Aggregator
from medperf.entities.cube import Cube
from medperf.utils import storage_path


class StartAggregator:
    @classmethod
    def run(cls, training_exp_id: int, agg_uid: int):
        """Sets approval status for an association between a benchmark and a aggregator or mlcube

        Args:
            benchmark_uid (int): Benchmark UID.
            approval_status (str): Desired approval status to set for the association.
            comms (Comms): Instance of Comms interface.
            ui (UI): Instance of UI interface.
            aggregator_uid (int, optional): Aggregator UID. Defaults to None.
            mlcube_uid (int, optional): MLCube UID. Defaults to None.
        """
        execution = cls(training_exp_id, agg_uid)
        execution.prepare()
        execution.validate()
        execution.prepare_agg_cert()
        execution.prepare_cube()
        with config.ui.interactive():
            execution.run_experiment()

    def __init__(self, training_exp_id, agg_uid) -> None:
        self.training_exp_id = training_exp_id
        self.agg_uid = agg_uid
        self.ui = config.ui

    def prepare(self):
        self.training_exp = TrainingExp.get(self.training_exp_id)
        self.ui.print(f"Training Execution: {self.training_exp.name}")
        self.aggregator = Aggregator.get(self.agg_uid)

    def validate(self):
        if self.aggregator.id is None:
            msg = "The provided aggregator is not registered."
            raise InvalidArgumentError(msg)

        training_exp_aggregator = config.comms.get_experiment_aggregator(
            self.training_exp.id
        )

        if self.aggregator.id != training_exp_aggregator["id"]:
            msg = "The provided aggregator is not associated."
            raise InvalidArgumentError(msg)

        if self.training_exp.state != "OPERATION":
            msg = "The provided training exp is not operational."
            raise InvalidArgumentError(msg)

    def prepare_agg_cert(self):
        association = config.comms.get_aggregator_association(
            self.training_exp.id, self.aggregator.id
        )
        cert = association["certificate"]
        cert_folder = os.path.join(
            config.training_exps_storage,
            str(self.training_exp.id),
            config.agg_cert_folder,
            str(self.aggregator.id),
        )
        cert_folder = storage_path(cert_folder)
        os.makedirs(cert_folder, exist_ok=True)
        cert_file = os.path.join(cert_folder, "cert.crt")
        with open(cert_file, "w") as f:
            f.write(cert)

        self.agg_cert_path = cert_folder

    def prepare_cube(self):
        self.cube = self.__get_cube(self.training_exp.fl_mlcube, "training")

    def __get_cube(self, uid: int, name: str) -> Cube:
        self.ui.text = f"Retrieving {name} cube"
        cube = Cube.get(uid)
        cube.download_run_files()
        self.ui.print(f"> {name} cube download complete")
        return cube

    def run_experiment(self):
        task = "start_aggregator"
        # just for now create some output folders (TODO)
        out_logs = os.path.join(self.training_exp.path, "logs")
        out_weights = os.path.join(self.training_exp.path, "weights")
        os.makedirs(out_logs, exist_ok=True)
        os.makedirs(out_weights, exist_ok=True)

        params = {
            "node_cert_folder": self.agg_cert_path,
            "ca_cert_folder": self.training_exp.cert_path,
            "network_config": self.aggregator.network_config_path,
            "collaborators": self.training_exp.cols_path,
            "output_logs": out_logs,
            "output_weights": out_weights,
        }

        self.ui.text = "Running Aggregator"
        self.cube.run(task=task, port=self.aggregator.port, **params)
