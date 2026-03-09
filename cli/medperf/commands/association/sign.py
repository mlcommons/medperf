from medperf.entities.benchmark import Benchmark
from medperf.entities.dataset import Dataset
from medperf.entities.model import Model
from medperf.encryption import Signing
from medperf.commands.certificate.utils import load_user_private_key
from medperf.account_management.account_management import get_medperf_user_data
from medperf.exceptions import MedperfException
from medperf import config


def sign_dataset_association(assoc):
    dataset_id = assoc["dataset"]
    benchmak_id = assoc["benchmark"]
    dataset = Dataset.get(dataset_id)
    dataset_hash = dataset.generated_uid
    user_private_key = load_user_private_key()
    signature = Signing().sign_prehashed(user_private_key, dataset_hash)
    body = {"signature": signature}
    config.comms.update_benchmark_dataset_association(benchmak_id, dataset_id, body)


def sign_model_association(assoc):
    model_id = assoc["model"]
    benchmark_id = assoc["benchmark"]
    model = Model.get(model_id)
    if model.is_container():
        model_hash = model.container.image_hash
        model_hash = model_hash.replace("sha256:", "")
    else:
        model_hash = model.asset.asset_hash
    user_private_key = load_user_private_key()
    signature = Signing().sign_prehashed(user_private_key, model_hash)
    body = {"signature": signature}
    config.comms.update_benchmark_model_association(benchmark_id, model_id, body)


class SignAssociations:
    @staticmethod
    def run(benchmark_uid: int):
        benchmark = Benchmark.get(benchmark_uid)
        current_user_id = get_medperf_user_data()["id"]
        if benchmark.owner != current_user_id:
            raise MedperfException(
                "You are not the owner of this benchmark and cannot sign its associations."
            )
        data_assocs = Benchmark.get_datasets_associations(
            benchmark_uid=benchmark_uid, approval_status="approved"
        )
        model_assocs = Benchmark.get_models_associations(
            benchmark_uid=benchmark_uid, approval_status="approved"
        )

        for assoc in data_assocs:
            sign_dataset_association(assoc)

        for assoc in model_assocs:
            sign_model_association(assoc)
