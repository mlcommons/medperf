from medperf import config
from medperf.account_management.account_management import get_medperf_user_data
from medperf.exceptions import InvalidArgumentError
from medperf.entities.ca import CA
from medperf.entities.training_exp import TrainingExp
from medperf.entities.cube import Cube
from medperf.utils import get_pki_assets_path, generate_tmp_path
from medperf.certificates import trust


class UpdatePlan:
    @classmethod
    def run(cls, training_exp_id: int, field_name: str, field_value: str):
        """Starts the aggregation server of a training experiment

        Args:
            training_exp_id (int): Training experiment UID.
        """
        execution = cls(training_exp_id, field_name, field_value)
        execution.prepare()
        execution.prepare_plan()
        execution.prepare_pki_assets()
        with config.ui.interactive():
            execution.prepare_admin_cube()
            execution.update_plan()

    def __init__(self, training_exp_id: int, field_name: str, field_value: str) -> None:
        self.training_exp_id = training_exp_id
        self.field_name = field_name
        self.field_value = field_value
        self.ui = config.ui

    def prepare(self):
        self.training_exp = TrainingExp.get(self.training_exp_id)
        self.ui.print(f"Training Experiment: {self.training_exp.name}")
        self.user_email: str = get_medperf_user_data()["email"]
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
        if not self.cube.has_task("update_plan"):
            raise InvalidArgumentError("This container doesn't support updating plans")

    def __get_cube(self, uid: int, name: str) -> Cube:
        self.ui.text = (
            "Retrieving and setting up training Container. This may take some time."
        )
        cube = Cube.get(uid)
        cube.download_run_files()
        self.ui.print(f"> Contaier '{name}' download complete")
        return cube

    def update_plan(self):
        env = {
            "MEDPERF_ADMIN_PARTICIPANT_CN": self.user_email,
            "MEDPERF_UPDATE_FIELD_NAME": self.field_name,
            "MEDPERF_UPDATE_FIELD_VALUE": self.field_value,
        }

        mounts = {
            "node_cert_folder": self.admin_pki_assets,
            "ca_cert_folder": self.ca.pki_assets,
            "plan_path": self.training_exp.plan_path,
            "temp_dir": self.temp_dir,
        }

        self.ui.text = "Updating plan"
        self.cube.run(task="update_plan", mounts=mounts, env=env, disable_network=False)
