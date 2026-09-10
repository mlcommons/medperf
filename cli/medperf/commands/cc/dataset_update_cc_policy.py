from medperf import config
from medperf.account_management.account_management import get_medperf_user_object
from medperf.cc.assets import set_permitted_grants, sync_cc_metadata
from medperf.cc.workloads import get_dataset_grants
from medperf.entities.dataset import Dataset
from medperf.exceptions import MedperfException
from medperf_cc import AssetKind


class DatasetUpdateCCPolicy:
    """Republishes which workloads may read this dataset.

    Whatever a sync leaves out stops being able to decrypt, which is the whole
    of how a grant is taken away."""

    @classmethod
    def run(cls, data_uid: int):
        dataset = Dataset.get(data_uid)
        if dataset.owner != get_medperf_user_object().id:
            raise MedperfException("User must be data owner")
        if not dataset.is_cc_configured():
            raise MedperfException(
                f"Dataset {dataset.id} is not configured for confidential computing."
            )
        with config.ui.interactive():
            config.ui.text = "Updating dataset confidential computing policy"
            grants = get_dataset_grants(dataset)
            set_permitted_grants(dataset, AssetKind.DATA, grants)
            sync_cc_metadata(dataset, config.comms.update_dataset)
