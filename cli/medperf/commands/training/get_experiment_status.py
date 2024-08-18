from medperf import config
from medperf.account_management.account_management import get_medperf_user_data
from medperf.entities.ca import CA
from medperf.entities.training_exp import TrainingExp
from medperf.entities.cube import Cube
from medperf.utils import get_pki_assets_path, generate_tmp_path, dict_pretty_print
from medperf.certificates import trust
import yaml


class GetExperimentStatus:
    @classmethod
    def run(cls, training_exp_id: int):
        """Starts the aggregation server of a training experiment

        Args:
            training_exp_id (int): Training experiment UID.
        """
        execution = cls(training_exp_id)
        execution.prepare()
        execution.prepare_plan()
        execution.prepare_pki_assets()
        with config.ui.interactive():
            execution.prepare_admin_cube()
            execution.get_experiment_status()
        execution.print_experiment_status()

    def __init__(self, training_exp_id: int) -> None:
        self.training_exp_id = training_exp_id
        self.ui = config.ui

    def prepare(self):
        self.training_exp = TrainingExp.get(self.training_exp_id)
        self.ui.print(f"Training Experiment: {self.training_exp.name}")
        self.user_email: str = get_medperf_user_data()["email"]
        self.status_output = self.training_exp.status_path
        self.temp_dir = generate_tmp_path()

    def prepare_plan(self):
        self.training_exp.prepare_plan()

    def prepare_pki_assets(self):
        ca = CA.from_experiment(self.training_exp_id)
        trust(ca)
        self.admin_pki_assets = get_pki_assets_path(self.user_email, ca.name)
        self.ca = ca

    def prepare_admin_cube(self):
        self.cube = self.__get_cube(self.training_exp.fl_admin_mlcube, "FL Admin")

    def __get_cube(self, uid: int, name: str) -> Cube:
        self.ui.text = (
            "Retrieving and setting up training MLCube. This may take some time."
        )
        cube = Cube.get(uid)
        cube.download_run_files()
        self.ui.print(f"> {name} cube download complete")
        return cube

    def get_experiment_status(self):
        env_dict = {"MEDPERF_ADMIN_PARTICIPANT_CN": self.user_email}
        params = {
            "node_cert_folder": self.admin_pki_assets,
            "ca_cert_folder": self.ca.pki_assets,
            "plan_path": self.training_exp.plan_path,
            "output_status_file": self.status_output,
            "temp_dir": self.temp_dir,
        }

        self.ui.text = "Getting training experiment status"
        self.cube.run(task="get_experiment_status", env_dict=env_dict, **params)

    def print_experiment_status(self):
        with open(self.status_output) as f:
            contents = yaml.safe_load(f)
        dict_pretty_print(contents)
