from medperf.asset_management.gcp_utils import (
    CCWorkloadID,
    GCPAssetConfig,
    GCPOperatorConfig,
)
from medperf.entities.dataset import Dataset
from medperf.entities.model import Model
from medperf.entities.user import User
from medperf.asset_management.asset_storage_manager import AssetStorageManager
from medperf.asset_management.asset_policy_manager import AssetPolicyManager
from medperf.asset_management.cc_operator import OperatorManager
from medperf.utils import tar, generate_tmp_path
import secrets
from medperf.exceptions import MedperfException
from medperf import config as medperf_config


def generate_encryption_key():
    return secrets.token_bytes(32)


def validate_cc_config(cc_config: dict, asset_name_prefix: str):
    if cc_config == {}:
        return

    cc_config["encrypted_asset_bucket_file"] = asset_name_prefix + ".enc"
    cc_config["encrypted_key_bucket_file"] = asset_name_prefix + "_key.enc"

    GCPAssetConfig(**cc_config)


def validate_cc_operator_config(cc_config: dict):
    if cc_config == {}:
        return
    GCPOperatorConfig(**cc_config)


def setup_dataset_for_cc(dataset: Dataset):
    if not dataset.is_cc_configured():
        return
    cc_config = dataset.get_cc_config()
    cc_policy = dataset.get_cc_policy()
    __verify_cloud_environment(cc_config)

    # create dataset asset
    medperf_config.ui.text = "Compressing dataset"
    asset_path = generate_tmp_path()
    tar(asset_path, [dataset.data_path, dataset.labels_path])

    __setup_asset_for_cc(cc_config, cc_policy, asset_path)


def setup_model_for_cc(model: Model):
    if not model.is_cc_configured():
        return
    cc_config = model.get_cc_config()
    cc_policy = model.get_cc_policy()
    if model.type != "ASSET":
        raise MedperfException(
            f"Model {model.id} is not a file-based asset and cannot be set up for confidential computing."
        )
    asset = model.asset_obj
    # create model asset
    asset_path = asset.get_archive_path()

    __verify_cloud_environment(cc_config)
    __setup_asset_for_cc(cc_config, cc_policy, asset_path, for_model=True)


def __verify_cloud_environment(cc_config: dict):
    AssetStorageManager(cc_config, None, None).setup()


def __setup_asset_for_cc(
    cc_config: dict,
    cc_policy: dict,
    asset_path: str,
    for_model: bool = False,
):
    # create encryption key
    encryption_key = generate_encryption_key()

    asset_storage_manager = AssetStorageManager(cc_config, asset_path, encryption_key)
    asset_policy_manager = AssetPolicyManager(cc_config, for_model=for_model)

    # storage
    asset_storage_manager.store_asset()

    # policy setup
    asset_policy_manager.setup_policy(cc_policy, encryption_key)
    del encryption_key


def update_dataset_cc_policy(dataset: Dataset, permitted_workloads: list[CCWorkloadID]):
    if not dataset.is_cc_configured():
        raise MedperfException(
            f"Dataset {dataset.id} does not have a configuration for confidential computing."
        )

    cc_config = dataset.get_cc_config()
    asset_policy_manager = AssetPolicyManager(cc_config)
    asset_policy_manager.configure_policy(permitted_workloads)


def update_model_cc_policy(model: Model, permitted_workloads: list[CCWorkloadID]):
    if not model.is_cc_configured():
        raise MedperfException(
            f"Model {model.id} does not have a configuration for confidential computing."
        )
    cc_config = model.get_cc_config()
    if model.type != "ASSET":
        raise MedperfException(
            f"Model {model.id} is not a file-based asset and cannot be set up for confidential computing."
        )

    asset_policy_manager = AssetPolicyManager(cc_config, for_model=True)
    asset_policy_manager.configure_policy(permitted_workloads)


def setup_operator(user: User):
    if not user.is_cc_configured():
        return

    cc_config = user.get_cc_config()
    operator_manager = OperatorManager(cc_config)
    operator_manager.setup()


def run_workload(
    docker_image: str,
    workload: CCWorkloadID,
    dataset_cc_config: dict,
    model_cc_config: dict,
    operator_cc_config: dict,
    result_collector_public_key: str,
):

    operator_manager = OperatorManager(operator_cc_config)
    operator_manager.run_workload(
        docker_image,
        workload,
        dataset_cc_config,
        model_cc_config,
        result_collector_public_key,
    )


def wait_for_workload(workload: CCWorkloadID, operator_cc_config: dict):
    operator_manager = OperatorManager(operator_cc_config)
    operator_manager.wait_for_workload_completion(workload)


def download_results(
    operator_cc_config: dict,
    workload: CCWorkloadID,
    private_key_bytes: bytes,
    results_path: str,
):
    operator_manager = OperatorManager(operator_cc_config)

    operator_manager.download_results(workload, private_key_bytes, results_path)


def workload_results_exists(operator_cc_config: dict, workload: CCWorkloadID) -> bool:
    operator_manager = OperatorManager(operator_cc_config)
    return operator_manager.results_exist(workload)
