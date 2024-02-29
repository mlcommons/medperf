import os

import medperf.config as config
from medperf.entities.training_exp import TrainingExp
from medperf.entities.cube import Cube
from medperf.utils import remove_path


class SubmitTrainingExp:
    @classmethod
    def run(cls, training_exp_info: dict):
        """Submits a new cube to the medperf platform
        Args:
            benchmark_info (dict): benchmark information
                expected keys:
                    name (str): benchmark name
                    description (str): benchmark description
                    docs_url (str): benchmark documentation url
                    demo_url (str): benchmark demo dataset url
                    demo_hash (str): benchmark demo dataset hash
                    data_preparation_mlcube (int): benchmark data preparation mlcube uid
                    reference_model_mlcube (int): benchmark reference model mlcube uid
                    evaluator_mlcube (int): benchmark data evaluator mlcube uid
        """
        ui = config.ui
        submission = cls(training_exp_info)

        with ui.interactive():
            ui.text = "Getting FL MLCube"
            submission.get_mlcube()
            ui.print("> Completed retrieving FL MLCube")
            ui.text = "Submitting TrainingExp to MedPerf"
            updated_benchmark_body = submission.submit()
        ui.print("Uploaded")
        submission.write(updated_benchmark_body)

    def __init__(self, training_exp_info: dict):
        self.ui = config.ui
        self.training_exp = TrainingExp(**training_exp_info)
        config.tmp_paths.append(self.training_exp.path)

    def get_mlcube(self):
        mlcube_id = self.training_exp.fl_mlcube
        cube = Cube.get(mlcube_id)
        # TODO: do we want to download run files?
        cube.download_run_files()

    def submit(self):
        updated_body = self.training_exp.upload()
        return updated_body

    def write(self, updated_body):
        remove_path(self.training_exp.path)
        training_exp = TrainingExp(**updated_body)
        training_exp.write()
