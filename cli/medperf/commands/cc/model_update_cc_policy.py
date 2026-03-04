from medperf.entities.certificate import Certificate
from medperf.entities.model import Model
from medperf.exceptions import MedperfException
from medperf.asset_management.asset_management import update_model_cc_policy
from medperf.asset_management.gcp_utils import CCWorkloadID
from medperf.entities.benchmark import Benchmark
from medperf.entities.dataset import Dataset
from medperf import config
from medperf.account_management.account_management import get_medperf_user_object
from medperf.entities.cube import Cube
from medperf.utils import get_string_hash
import base64


def get_permitted_workloads(model: Model):
    user_obj = get_medperf_user_object()
    if model.owner != user_obj.id:
        raise MedperfException("User must be model owner")
    asset = model.asset

    permitted_workloads = []
    assocs = config.comms.get_model_benchmarks_associations(model.id)
    for assoc in assocs:
        benchmark_id = assoc["benchmark"]
        benchmark = Benchmark.get(benchmark_id)
        evaluator = Cube.get(benchmark.data_evaluator_mlcube)
        datasets_certs = config.comms.get_benchmark_datasets_certificates(benchmark_id)
        mappings = {}
        for cert in datasets_certs:
            owner = cert.pop("owner")
            user_id = owner["id"]
            cert_obj = Certificate(**cert)
            mappings[user_id] = cert_obj.public_key()

        datasets_associations = config.comms.get_benchmark_datasets_associations(
            benchmark_id
        )
        for dataset_assoc in datasets_associations:
            dataset = Dataset.get(dataset_assoc["dataset"])
            # note: if the dataset owner doesn't have a certificate, they won't be able to participate
            public_key_bytes = mappings[dataset.owner]
            public_key_b64 = base64.b64encode(public_key_bytes)
            public_key_hash = get_string_hash(public_key_b64)
            workload_info = CCWorkloadID(
                data_hash=dataset.generated_uid,
                model_hash=asset.asset_hash,
                script_hash=evaluator.image_hash,
                result_collector_hash=public_key_hash,
                data_id=dataset.id,
                model_id=model.id,
                script_id=evaluator.id,
            )
            permitted_workloads.append(workload_info)

    return permitted_workloads


class ModelUpdateCCPolicy:
    @classmethod
    def run(cls, model_uid: int):
        model = Model.get(model_uid)
        if not model.is_cc_configured():
            raise MedperfException(
                f"Model {model.id} is not configured for confidential computing."
            )
        permitted_workloads = get_permitted_workloads(model)
        update_model_cc_policy(model, permitted_workloads)
