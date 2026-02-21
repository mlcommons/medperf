import argparse
import os
import json
from assets.factory import storage_manager, key_manager
from utils import untar
from crypto import SymmetricEncryption, get_file_hash, get_folders_hash, get_string_hash

decryption = SymmetricEncryption()
decryption.check()


def __check_folder_hash(folder_path: str, expected_hash: str) -> None:
    actual_hash = get_folders_hash(os.listdir(folder_path))
    if actual_hash != expected_hash:
        raise ValueError(
            f"Asset folder hash mismatch: expected {expected_hash}, got {actual_hash}"
        )


def __check_file_hash(asset_path: str, expected_hash: str) -> None:
    actual_hash = get_file_hash(asset_path)
    if actual_hash != expected_hash:
        raise ValueError(
            f"Asset hash mismatch: expected {expected_hash}, got {actual_hash}"
        )


def __check_string_hash(value: str, expected_hash: str) -> None:
    actual_hash = get_string_hash(value)
    if actual_hash != expected_hash:
        raise ValueError(
            f"String hash mismatch: expected {expected_hash}, got {actual_hash}"
        )


def __setup_asset_archive(asset_config: dict) -> str:

    tmp_files = os.getenv("TMP_FILES")
    os.makedirs(tmp_files, exist_ok=True)

    tmp_encrypted_asset_path = os.path.join(tmp_files, "encrypted_asset_files.enc")
    tmp_key_path = os.path.join(tmp_files, "decryption_key.gpg")
    tmp_asset_archive = os.path.join(tmp_files, "asset.tar.gz")

    storage_manager_instance = storage_manager(asset_config)
    storage_manager_instance.initialize()
    storage_manager_instance.get_asset(tmp_encrypted_asset_path)

    key_manager_instance = key_manager(asset_config)
    key_manager_instance.initialize()
    key_manager_instance.get_key(tmp_key_path)

    decryption.decrypt_file(tmp_encrypted_asset_path, tmp_key_path, tmp_asset_archive)
    os.remove(tmp_encrypted_asset_path)
    os.remove(tmp_key_path)
    return tmp_asset_archive


def __untar_dataset(
    tmp_asset_archive: str, output_folder: str, expected_asset_hash: str
) -> None:
    os.makedirs(output_folder, exist_ok=True)
    untar(tmp_asset_archive, output_folder)
    __check_folder_hash(output_folder, expected_asset_hash)


def __untar_model(
    tmp_asset_archive: str, output_folder: str, expected_asset_hash: str
) -> None:
    __check_file_hash(tmp_asset_archive, expected_asset_hash)
    os.makedirs(output_folder, exist_ok=True)
    untar(tmp_asset_archive, output_folder)


def setup_assets(args) -> None:

    data_files_path = args.data_files
    model_files_path = args.model_files

    # get configs from environment variables
    data_config_str = os.getenv("DATA_CONFIG")
    model_config_str = os.getenv("MODEL_CONFIG")
    expected_data_hash = os.getenv("EXPECTED_DATA_HASH")
    expected_model_hash = os.getenv("EXPECTED_MODEL_HASH")

    data_config = json.loads(data_config_str)
    model_config = json.loads(model_config_str)

    tmp_data_archive = __setup_asset_archive(data_config)
    tmp_model_archive = __setup_asset_archive(model_config)

    __untar_dataset(tmp_data_archive, data_files_path, expected_data_hash)
    __untar_model(tmp_model_archive, model_files_path, expected_model_hash)

    # also, verify early that the result collector's public key hash is as expected
    result_collector_public_key_hash = os.getenv("EXPECTED_RESULT_COLLECTOR_HASH")
    public_key = os.getenv("RESULT_COLLECTOR")
    __check_string_hash(public_key, result_collector_public_key_hash)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data-files",
        required=True,
        help="Folder to put data files in",
    )

    parser.add_argument(
        "--model-files",
        required=True,
        help="Folder to put model files in",
    )

    args = parser.parse_args()
    setup_assets(args)
