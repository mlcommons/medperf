from medperf.entities.asset import Asset
from medperf.entities.dataset import Dataset
from medperf.entities.model import Model
from medperf.entities.user import User
from medperf.asset_management.asset_storage_manager import AssetStorageManager
from medperf.asset_management.asset_policy_manager import AssetPolicyManager
from medperf.asset_management.cc_operator import OperatorManager
from medperf.utils import tar, generate_tmp_path
import secrets
import os
from medperf import config


def generate_encryption_key(encryption_key_file: str):
    with open(encryption_key_file, "wb") as f:
        pass
    os.chmod(encryption_key_file, 0o700)
    with open(encryption_key_file, "ab") as f:
        f.write(secrets.token_bytes(32))


def setup_dataset_for_cc(dataset: Dataset):
    cc_config = dataset.get_cc_config()
    cc_policy = dataset.get_cc_policy()
    if not cc_config:
        raise ValueError(
            f"Dataset {dataset.id} does not have a configuration for confidential computing."
        )
    if not cc_policy:
        raise ValueError(
            f"Dataset {dataset.id} does not have a policy for confidential computing."
        )
    # create dataset asset
    asset_path = generate_tmp_path()
    tar(asset_path, [dataset.data_path, dataset.labels_path])

    # create encryption key
    encryption_key_folder = os.path.join(
        config.cc_artifacts_dir, "dataset" + str(dataset.id)
    )
    os.makedirs(encryption_key_folder, exist_ok=True)
    encryption_key_file = os.path.join(encryption_key_folder, "encryption_key.bin")
    generate_encryption_key(encryption_key_file)

    __setup_asset_for_cc(cc_config, cc_policy, asset_path, encryption_key_file)


def setup_model_for_cc(model: Model):
    cc_config = model.get_cc_config()
    cc_policy = model.get_cc_policy()
    if not cc_config:
        raise ValueError(
            f"Model {model.id} does not have a configuration for confidential computing."
        )
    if not cc_policy:
        raise ValueError(
            f"Model {model.id} does not have a policy for confidential computing."
        )
    if model.type != "ASSET":
        raise ValueError(
            f"Model {model.id} is not a file-based asset and cannot be set up for confidential computing."
        )

    asset = Asset.get(model.asset)
    # create model asset
    asset_path = asset.get_archive_path()

    # create encryption key
    encryption_key_folder = os.path.join(
        config.cc_artifacts_dir, "model" + str(model.id)
    )
    os.makedirs(encryption_key_folder, exist_ok=True)
    encryption_key_file = os.path.join(encryption_key_folder, "encryption_key.bin")
    generate_encryption_key(encryption_key_file)

    __setup_asset_for_cc(cc_config, cc_policy, asset_path, encryption_key_file)


def __setup_asset_for_cc(
    cc_config: dict, cc_policy: dict, asset_path: str, encryption_key_file: str
):
    # asset storage setup
    asset_storage_manager = AssetStorageManager(
        cc_config, asset_path, encryption_key_file
    )
    asset_storage_manager.setup()
    asset_storage_manager.store_asset()

    # policy setup
    asset_policy_manager = AssetPolicyManager(cc_config, encryption_key_file)
    asset_policy_manager.setup()
    asset_policy_manager.setup_policy(cc_policy)


def update_dataset_cc_policy(dataset: Dataset, permitted_workloads: list):
    cc_config = dataset.get_cc_config()
    if not cc_config:
        raise ValueError(
            f"Dataset {dataset.id} does not have a configuration for confidential computing."
        )

    encryption_key_folder = os.path.join(
        config.cc_artifacts_dir, "dataset" + str(dataset.id)
    )
    encryption_key_file = os.path.join(encryption_key_folder, "encryption_key.bin")

    asset_policy_manager = AssetPolicyManager(cc_config, encryption_key_file)
    asset_policy_manager.configure_policy(permitted_workloads)


def update_model_cc_policy(model: Model, permitted_workloads: list):
    cc_config = model.get_cc_config()
    if not cc_config:
        raise ValueError(
            f"Model {model.id} does not have a configuration for confidential computing."
        )
    if model.type != "ASSET":
        raise ValueError(
            f"Model {model.id} is not a file-based asset and cannot be set up for confidential computing."
        )

    encryption_key_folder = os.path.join(
        config.cc_artifacts_dir, "model" + str(model.id)
    )
    encryption_key_file = os.path.join(encryption_key_folder, "encryption_key.bin")

    asset_policy_manager = AssetPolicyManager(cc_config, encryption_key_file)
    asset_policy_manager.configure_policy(permitted_workloads)


def setup_operator(user: User):
    cc_config = user.get_cc_config()
    if not cc_config:
        raise ValueError(
            "User does not have a configuration for confidential computing."
        )

    operator_manager = OperatorManager(cc_config)
    operator_manager.setup()


def run_workload(
    docker_image: str,
    workload_dict: dict,
    dataset_cc_config: dict,
    model_cc_config: dict,
    operator_cc_config: dict,
    result_collector_public_key: str,
):

    operator_manager = OperatorManager(operator_cc_config)
    operator_manager.run_workload(
        docker_image,
        workload_dict,
        dataset_cc_config,
        model_cc_config,
        workload_dict["EXPECTED_DATA_HASH"],
        workload_dict["EXPECTED_MODEL_HASH"],
        result_collector_public_key,
    )
