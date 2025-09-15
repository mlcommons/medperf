import base64
from medperf.account_management.account_management import get_medperf_user_data
import medperf.config as config
from medperf.entities.aggregator import Aggregator
from medperf.entities.training_exp import TrainingExp
from medperf.entities.cube import Cube
from medperf.exceptions import CleanExit, InvalidArgumentError
from medperf.utils import approval_prompt, dict_pretty_print, generate_tmp_path, untar
import os

import yaml


class SetPlan:
    @classmethod
    def run(
        cls, training_exp_id: int, training_config_path: str, approval: bool = False
    ):
        """Creates and submits the training plan
        Args:
            training_exp_id (int): training experiment
            training_config_path (str): path to a training config file
            approval (bool): skip approval
        """
        planset = cls(training_exp_id, training_config_path, approval)
        planset.validate()
        planset.prepare()
        planset.create_plan()
        planset.update()
        planset.write()
        planset.upload_training_kits()

    def __init__(self, training_exp_id: int, training_config_path: str, approval: bool):
        self.ui = config.ui
        self.training_exp_id = training_exp_id
        self.training_config_path = os.path.abspath(training_config_path)
        self.approved = approval
        self.plan_out_path = generate_tmp_path()
        self.kits_path = generate_tmp_path()
        self.kits_metadata = generate_tmp_path()

    def validate(self):
        if not os.path.exists(self.training_config_path):
            raise InvalidArgumentError("Provided training config path does not exist")

    def prepare(self):
        self.training_exp = TrainingExp.get(self.training_exp_id)
        self.aggregator = Aggregator.from_experiment(self.training_exp_id)
        self.mlcube = self.__get_cube(self.training_exp.fl_mlcube, "FL")
        self.aggregator.prepare_config()

    def __get_cube(self, uid: int, name: str) -> Cube:
        self.ui.text = f"Retrieving container '{name}'"
        cube = Cube.get(uid)
        cube.download_run_files()
        self.ui.print(f"> Container '{name}' download complete")
        return cube

    def create_plan(self):
        """Auto-generates dataset UIDs for both input and output paths"""
        participant_label = get_medperf_user_data()["email"]
        env = {"MEDPERF_PARTICIPANT_LABEL": participant_label}
        mounts = {
            "training_config_path": self.training_config_path,
            "aggregator_config_path": self.aggregator.config_path,
            "plan_path": self.plan_out_path,
            "kits_path": self.kits_path,
            "kits_metadata": self.kits_metadata,
        }
        self.mlcube.run("generate_plan", env=env, mounts=mounts)

    def update(self):
        with open(self.plan_out_path) as f:
            plan = yaml.safe_load(f)
        self.training_exp.plan = plan
        body = {"plan": plan}
        dict_pretty_print(body)
        msg = (
            "This is the training plan that will be submitted and used by the participants."
            " Do you confirm?[Y/n] "
        )
        self.approved = self.approved or approval_prompt(msg)

        if self.approved:
            config.comms.update_training_exp(self.training_exp.id, body)
            return

        raise CleanExit("Setting the training plan was cancelled")

    def write(self) -> str:
        """Writes the registration into disk
        Args:
            filename (str, optional): name of the file. Defaults to config.reg_file.
        """
        self.training_exp.write()

    def upload_training_kits(self):
        if not os.path.exists(self.kits_path) or len(os.listdir(self.kits_path)) == 0:
            return

        with open(self.kits_metadata) as f:
            metadata = yaml.safe_load(f)
        admin_kit_path = os.path.join(self.kits_path, metadata["admin"])
        server_kit_path = os.path.join(self.kits_path, metadata["server"])
        with open(server_kit_path, "rb") as f:
            server_kit = base64.b64encode(f.read()).decode()

        clients_kits = []
        for client in metadata["clients"]:
            client_kit_path = os.path.join(self.kits_path, metadata["clients"][client])
            with open(client_kit_path, "rb") as f:
                clients_kits.append(
                    {"email": client, "kit": base64.b64encode(f.read()).decode()}
                )

        os.makedirs(self.training_exp.admin_kit, exist_ok=True)

        untar(admin_kit_path, extract_to=self.training_exp.admin_kit)

        config.comms.upload_clients_kits(self.training_exp_id, clients_kits)
        config.comms.upload_aggregator_kit(
            self.training_exp_id,
            {"kit": server_kit, "aggregator": self.aggregator.id},
        )
