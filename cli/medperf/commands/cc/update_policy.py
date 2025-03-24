from medperf.entities.kbs import KBS
from medperf.entities.dataset import Dataset
from medperf.entities.cube import Cube
from medperf.exceptions import MedperfException
import medperf.config as config

class UpdatePolicy:
    @classmethod
    def run(cls, dataset_id, model_id):
        if dataset_id is not None and model_id is not None:
            raise MedperfException("one ID should be given")
        
        if dataset_id is None and model_id is None:
            raise MedperfException("one ID should be given")

        if dataset_id:
            dataset = Dataset.get(dataset_id)
            kbs: KBS = KBS.get(dataset.user_metadata["kbs"])
        else:
            cube = Cube.get(model_id)
            kbs: KBS = KBS.get(cube.user_metadata["kbs"])
        
        with open(config.kbs_policy_template_path) as f:
            contents = f.read()
        
        with open(kbs.policy_path, "w") as f:
            f.write(contents)
        
