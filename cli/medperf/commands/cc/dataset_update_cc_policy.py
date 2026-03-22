from medperf.entities.model import Model
from medperf.entities.benchmark import Benchmark
from medperf.entities.dataset import Dataset
from medperf.exceptions import MedperfException
from medperf.asset_management.asset_management import update_dataset_cc_policy
from medperf.asset_management.gcp_utils import CCWorkloadID
from medperf import config
from medperf.account_management.account_management import get_medperf_user_object
from medperf.entities.cube import Cube
from medperf.entities.certificate import Certificate
from medperf.utils import get_string_hash
from medperf.commands.certificate.utils import current_user_certificate_status
import base64


def get_permitted_workloads(dataset: Dataset):
    user_obj = get_medperf_user_object()
    if dataset.owner != user_obj.id:
        raise MedperfException("User must be data owner")
    status_dict = current_user_certificate_status()
    user_cert = None
    if status_dict["should_be_submitted"]:
        user_cert = Certificate.get_local_user_certificate()
    elif status_dict["no_action_required"]:
        user_cert = status_dict["user_cert_object"]

    if not user_cert:
        raise MedperfException("User must have a certificate to update cc policy")
    public_key_bytes = user_cert.public_key()
    public_key_b64 = base64.b64encode(public_key_bytes)
    public_key_hash = get_string_hash(public_key_b64)

    permitted_workloads = []
    assocs = config.comms.get_dataset_benchmarks_associations(dataset.id)
    for assoc in assocs:
        benchmark_id = assoc["benchmark"]
        benchmark = Benchmark.get(benchmark_id)
        evaluator = Cube.get(benchmark.data_evaluator_mlcube)
        if evaluator.is_script():
            script_hash = evaluator.image_hash
        else:
            ref_model = Model.get(benchmark.reference_model)
            script_hash = ref_model.container_obj.image_hash
        model_assocs = config.comms.get_benchmark_models_associations(benchmark_id)
        for model_assoc in model_assocs:
            model = Model.get(model_assoc["model"])
            if not model.requires_cc():
                continue
            asset = model.asset_obj
            workload_info = CCWorkloadID(
                data_hash=dataset.generated_uid,
                model_hash=asset.asset_hash,
                script_hash=script_hash,
                result_collector_hash=public_key_hash,
                data_id=dataset.id,
                model_id=model.id,
                script_id=evaluator.id,
            )
            permitted_workloads.append(workload_info)

    return permitted_workloads


class DatasetUpdateCCPolicy:
    @classmethod
    def run(cls, data_uid: int):
        dataset = Dataset.get(data_uid)
        if not dataset.is_cc_configured():
            raise MedperfException(
                f"Dataset {dataset.id} is not configured for confidential computing."
            )
        with config.ui.interactive():
            config.ui.text = "Updating dataset confidential computing policy"
            permitted_workloads = get_permitted_workloads(dataset)
            update_dataset_cc_policy(dataset, permitted_workloads)
            dataset.set_last_synced()
            body = {"user_metadata": dataset.user_metadata}
            config.comms.update_dataset(dataset.id, body)
