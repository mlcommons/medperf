import os
from medperf import config
from medperf.exceptions import InvalidArgumentError
from medperf.entities.training_exp import TrainingExp
from medperf.entities.dataset import Dataset
from medperf.entities.cube import Cube
from medperf.entities.aggregator import Aggregator
from medperf.utils import get_dataset_common_name


class TrainingExecution:
    @classmethod
    def run(cls, training_exp_id: int, data_uid: int):
        """Sets approval status for an association between a benchmark and a dataset or mlcube

        Args:
            benchmark_uid (int): Benchmark UID.
            approval_status (str): Desired approval status to set for the association.
            comms (Comms): Instance of Comms interface.
            ui (UI): Instance of UI interface.
            dataset_uid (int, optional): Dataset UID. Defaults to None.
            mlcube_uid (int, optional): MLCube UID. Defaults to None.
        """
        execution = cls(training_exp_id, data_uid)
        execution.prepare()
        execution.validate()
        execution.prepare_data_cert()
        execution.prepare_network_config()
        execution.prepare_cube()
        with config.ui.interactive():
            execution.run_experiment()

    def __init__(self, training_exp_id, data_uid) -> None:
        self.training_exp_id = training_exp_id
        self.data_uid = data_uid
        self.ui = config.ui

    def prepare(self):
        self.training_exp = TrainingExp.get(self.training_exp_id)
        self.ui.print(f"Training Execution: {self.training_exp.name}")
        self.dataset = Dataset.get(self.data_uid)

    def validate(self):
        if self.dataset.id is None:
            msg = "The provided dataset is not registered."
            raise InvalidArgumentError(msg)

        if self.dataset.id not in self.training_exp.datasets:
            msg = "The provided dataset is not associated."
            raise InvalidArgumentError(msg)

        if self.training_exp.state != "OPERATION":
            msg = "The provided training exp is not operational."
            raise InvalidArgumentError(msg)

    def prepare_data_cert(self):
        association = config.comms.get_training_dataset_association(
            self.training_exp.id, self.dataset.id
        )
        cert = association["certificate"]
        cert_folder = os.path.join(
            config.training_folder,
            str(self.training_exp.id),
            config.data_cert_folder,
            str(self.dataset.id),
        )
        os.makedirs(cert_folder, exist_ok=True)
        cert_file = os.path.join(cert_folder, "cert.crt")
        with open(cert_file, "w") as f:
            f.write(cert)

        self.data_cert_path = cert_folder

    def prepare_network_config(self):
        aggregator = config.comms.get_experiment_aggregator(self.training_exp.id)
        aggregator = Aggregator.get(aggregator["id"])
        self.network_config_path = aggregator.network_config_path

    def prepare_cube(self):
        self.cube = self.__get_cube(self.training_exp.fl_mlcube, "training")

    def __get_cube(self, uid: int, name: str) -> Cube:
        self.ui.text = f"Retrieving {name} cube"
        cube = Cube.get(uid)
        cube.download_run_files()
        self.ui.print(f"> {name} cube download complete")
        return cube

    def run_experiment(self):
        task = "train"
        dataset_cn = get_dataset_common_name("", self.dataset.id, self.training_exp.id)
        env_dict = {"COLLABORATOR_CN": dataset_cn}

        # just for now create some output folders (TODO)
        out_logs = os.path.join(self.training_exp.path, "data_logs", dataset_cn)
        os.makedirs(out_logs, exist_ok=True)

        params = {
            "data_path": self.dataset.data_path,
            "labels_path": self.dataset.labels_path,
            "node_cert_folder": self.data_cert_path,
            "ca_cert_folder": self.training_exp.cert_path,
            "network_config": self.network_config_path,
            "output_logs": out_logs,
        }
        self.ui.text = "Training"
        self.cube.run(task=task, env_dict=env_dict, **params)
