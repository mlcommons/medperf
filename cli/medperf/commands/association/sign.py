from medperf.entities.benchmark import Benchmark
from medperf.commands.association.utils import (
    sign_dataset_association,
    sign_model_association,
)
from medperf.account_management.account_management import get_medperf_user_data
from medperf.exceptions import MedperfException


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
