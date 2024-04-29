from medperf import config
from medperf.account_management.account_management import get_medperf_user_data
from medperf.entities.ca import CA
from medperf.entities.event import TrainingEvent
from medperf.exceptions import InvalidArgumentError
from medperf.entities.training_exp import TrainingExp
from medperf.entities.dataset import Dataset
from medperf.entities.cube import Cube
from medperf.utils import get_pki_assets_path, get_participant_label
from medperf.certificates import trust


class TrainingExecution:
    @classmethod
    def run(cls, training_exp_id: int, data_uid: int):
        """Starts the aggregation server of a training experiment

        Args:
            training_exp_id (int): Training experiment UID.
        """
        execution = cls(training_exp_id, data_uid)
        execution.prepare()
        execution.validate()
        execution.prepare_training_cube()
        execution.prepare_plan()
        execution.prepare_pki_assets()
        with config.ui.interactive():
            execution.run_experiment()

    def __init__(self, training_exp_id: int, data_uid: int) -> None:
        self.training_exp_id = training_exp_id
        self.data_uid = data_uid
        self.ui = config.ui

    def prepare(self):
        self.training_exp = TrainingExp.get(self.training_exp_id)
        self.ui.print(f"Training Execution: {self.training_exp.name}")
        self.event = TrainingEvent.from_experiment(self.training_exp_id)
        self.dataset = Dataset.get(self.data_uid)
        self.user_email: str = get_medperf_user_data()["email"]

    def validate(self):
        if self.dataset.id is None:
            msg = "The provided dataset is not registered."
            raise InvalidArgumentError(msg)

        if self.dataset.state != "OPERATION":
            msg = "The provided dataset is not operational."
            raise InvalidArgumentError(msg)

        if self.event.finished():
            msg = "The provided training experiment has to start a training event."
            raise InvalidArgumentError(msg)

        if self.dataset.id not in self.training_exp.get_datasets_uids():
            msg = "The provided dataset is not associated."
            raise InvalidArgumentError(msg)

    def prepare_training_cube(self):
        self.cube = self.__get_cube(self.training_exp.fl_mlcube, "FL")

    def __get_cube(self, uid: int, name: str) -> Cube:
        self.ui.text = f"Retrieving {name} cube"
        cube = Cube.get(uid)
        cube.download_run_files()
        self.ui.print(f"> {name} cube download complete")
        return cube

    def prepare_plan(self):
        self.training_exp.prepare_plan()

    def prepare_pki_assets(self):
        ca = CA.from_experiment(self.training_exp_id)
        trust(ca)
        self.dataset_pki_assets = get_pki_assets_path(self.user_email, ca.name)
        self.ca = ca

    def run_experiment(self):
        participant_label = get_participant_label(self.user_email, self.dataset.id)
        env_dict = {"MEDPERF_PARTICIPANT_LABEL": participant_label}
        params = {
            "data_path": self.dataset.data_path,
            "labels_path": self.dataset.labels_path,
            "node_cert_folder": self.dataset_pki_assets,
            "ca_cert_folder": self.ca.pki_assets,
            "plan_path": self.training_exp.plan_path,
            "output_logs": self.event.out_logs,
        }

        self.ui.text = "Running Training"
        self.cube.run(task="train", env_dict=env_dict, **params)
