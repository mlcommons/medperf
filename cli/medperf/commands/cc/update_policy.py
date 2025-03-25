from medperf.entities.kbs import KBS
from medperf.entities.dataset import Dataset
from medperf.entities.benchmark import Benchmark
from medperf.entities.cube import Cube
from medperf.exceptions import MedperfException
import medperf.config as config
from medperf.utils import create_initdata_util, generate_tmp_path
import os


class UpdatePolicy:
    @classmethod
    def run(cls, dataset_id, model_id, benchmark_id):
        if dataset_id is not None and model_id is not None:
            raise MedperfException("one ID should be given")

        if dataset_id is None and model_id is None:
            raise MedperfException("one ID should be given")

        benchmark = Benchmark.get(benchmark_id)
        evaluator = Cube.get(benchmark.data_evaluator_mlcube)

        if dataset_id:
            dataset = Dataset.get(dataset_id)
            kbs: KBS = KBS.get(dataset.user_metadata["kbs"])
            model_id = Benchmark.get_models_uids(benchmark_id)[0]
            model = Cube.get(model_id)
        else:
            cube = Cube.get(model_id)
            kbs: KBS = KBS.get(cube.user_metadata["kbs"])
            model = cube

        model_kbs: KBS = KBS.get(model.user_metadata["kbs"])
        attest_service: KBS = KBS.get(model_kbs.config["as"])
        initdata, initpath = create_initdata_util(model, evaluator, model_kbs, attest_service)
        outpath = generate_tmp_path()
        script = os.path.join(os.path.dirname(__file__), "scripts/calculate_initdata_digest.sh")
        os.system(f"bash {script} {initpath} {outpath}")
        with open(outpath) as f:
            val = f.read().strip().strip("\n")

        with open(config.kbs_policy_template_path) as f:
            contents = f.read()

        contents = contents.format(digest=val)
        with open(kbs.policy_path, "w") as f:
            f.write(contents)
