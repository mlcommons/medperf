from medperf import config
from medperf.account_management.account_management import get_medperf_user_data
from medperf.entities.ca import CA
from medperf.entities.training_exp import TrainingExp
from medperf.entities.cube import Cube
from medperf.utils import (
    get_pki_assets_path,
    generate_tmp_path,
    dict_pretty_print,
    remove_path,
)
from medperf.certificates import trust
import yaml
import os


class GetExperimentStatus:
    @classmethod
    def run(cls, training_exp_id: int, silent: bool = False):
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
        if not silent:
            execution.print_experiment_status()
        execution.store_status()

    def __init__(self, training_exp_id: int) -> None:
        self.training_exp_id = training_exp_id
        self.ui = config.ui

    def prepare(self):
        self.training_exp = TrainingExp.get(self.training_exp_id)
        self.ui.print(f"Training Experiment: {self.training_exp.name}")
        self.user_email: str = get_medperf_user_data()["email"]
        self.status_output = generate_tmp_path()
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
            "Retrieving and setting up training Container. This may take some time."
        )
        cube = Cube.get(uid)
        cube.download_run_files()
        self.ui.print(f"> Container '{name}' download complete")
        return cube

    def get_experiment_status(self):
        env = {
            "MEDPERF_ADMIN_PARTICIPANT_CN": self.user_email,
            "MEDPERF_PARTICIPANT_LABEL": self.user_email,
        }
        mounts = {
            "node_cert_folder": self.admin_pki_assets,
            "ca_cert_folder": self.ca.pki_assets,
            "plan_path": self.training_exp.plan_path,
            "output_status_file": self.status_output,
            "temp_dir": self.temp_dir,
            "fl_workspace": self.training_exp.get_admin_kit_path(),
        }

        self.ui.text = "Getting training experiment status"
        self.cube.run(
            task="get_experiment_status", mounts=mounts, env=env, disable_network=False
        )

    def print_experiment_status(self):
        with open(self.status_output) as f:
            contents = yaml.safe_load(f)
        dict_pretty_print(contents, skip_none_values=False)

    def store_status(self):
        new_status_path = self.training_exp.status_path
        remove_path(new_status_path)
        os.rename(self.status_output, new_status_path)
