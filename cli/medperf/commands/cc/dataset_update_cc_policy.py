from medperf.entities.asset import Asset
from medperf.entities.model import Model
from medperf.entities.benchmark import Benchmark
from medperf.entities.dataset import Dataset
from medperf.exceptions import MedperfException
from medperf.asset_management.asset_management import update_dataset_cc_policy
from medperf import config
from medperf.account_management.account_management import get_medperf_user_object
from medperf.entities.cube import Cube
from medperf.commands.certificate.utils import current_user_certificate_status
from medperf.utils import get_string_hash
import base64


def get_permitted_workloads(dataset: Dataset):
    user_obj = get_medperf_user_object()
    if dataset.owner != user_obj.id:
        raise MedperfException("User must be data owner")
    user_cert = current_user_certificate_status()["user_cert_object"]
    if not user_cert:
        raise MedperfException("User must have a certificate to update cc policy")
    public_key_bytes = user_cert.public_key
    public_key_b64 = base64.b64encode(public_key_bytes)
    public_key_hash = get_string_hash(public_key_b64)

    permitted_workloads = []
    assocs = config.comms.get_dataset_benchmarks_associations(dataset.id)
    for assoc in assocs:
        benchmark_id = assoc["benchmark"]
        benchmark = Benchmark.get(benchmark_id)
        evaluator = Cube.get(benchmark.data_evaluator_mlcube)
        eval_hash = evaluator.image_hash
        model_assocs = config.comms.get_benchmark_models_associations(benchmark_id)
        for model_assoc in model_assocs:
            model = Model.get(model_assoc["model"])
            asset = Asset.get(model.asset)
            model_hash = asset.asset_hash
            permitted_workloads.append(
                {
                    "EXPECTED_DATA_HASH": dataset.generated_uid,
                    "EXPECTED_MODEL_HASH": model_hash,
                    "image_digest": eval_hash,
                    "EXPECTED_RESULT_COLLECTOR_HASH": public_key_hash,
                }
            )

    return permitted_workloads


class DatasetUpdateCCPolicy:
    @classmethod
    def run(cls, data_uid: int):
        dataset = Dataset.get(data_uid)
        if not dataset.is_cc_configured():
            raise MedperfException(
                f"Dataset {dataset.id} is not configured for confidential computing."
            )
        permitted_workloads = get_permitted_workloads(dataset)

        update_dataset_cc_policy(dataset, permitted_workloads)
