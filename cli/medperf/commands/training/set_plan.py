import medperf.config as config
from medperf.entities.aggregator import Aggregator
from medperf.entities.training_exp import TrainingExp
from medperf.entities.cube import Cube
from medperf.exceptions import CleanExit, InvalidArgumentError
from medperf.utils import approval_prompt, dict_pretty_print, generate_tmp_path
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

    def __init__(self, training_exp_id: int, training_config_path: str, approval: bool):
        self.ui = config.ui
        self.training_exp_id = training_exp_id
        self.training_config_path = os.path.abspath(training_config_path)
        self.approved = approval
        self.plan_out_path = generate_tmp_path()

    def validate(self):
        if not os.path.exists(self.training_config_path):
            raise InvalidArgumentError("Provided training config path does not exist")

    def prepare(self):
        self.training_exp = TrainingExp.get(self.training_exp_id)
        self.aggregator = Aggregator.from_experiment(self.training_exp_id)
        self.mlcube = self.__get_cube(self.training_exp.fl_mlcube, "FL")
        self.aggregator.prepare_config()

    def __get_cube(self, uid: int, name: str) -> Cube:
        self.ui.text = f"Retrieving {name} cube"
        cube = Cube.get(uid)
        cube.download_run_files()
        self.ui.print(f"> {name} cube download complete")
        return cube

    def create_plan(self):
        """Auto-generates dataset UIDs for both input and output paths"""
        params = {
            "training_config_path": self.training_config_path,
            "aggregator_config_path": self.aggregator.config_path,
            "plan_path": self.plan_out_path,
        }
        self.mlcube.run("generate_plan", **params)

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
