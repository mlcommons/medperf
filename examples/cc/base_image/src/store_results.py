import argparse
import os
import json
from assets.factory import result_manager
from utils import tar
from crypto import AsymmetricEncryption, SymmetricEncryption, generate_encryption_key
import base64


def store_results(args) -> None:

    result_files_path = args.result_files

    # get configs from environment variables
    result_config_str = os.getenv("RESULT_CONFIG")
    result_config = json.loads(result_config_str)

    # tar the results and write to storage
    tmp_files = os.getenv("TMP_FILES")
    os.makedirs(tmp_files, exist_ok=True)

    tmp_result_archive = os.path.join(tmp_files, "result.tar.gz")
    tar(output_path=tmp_result_archive, folder_path=result_files_path)

    # encrypt file
    encryption_key_file = os.path.join(tmp_files, "tmp_encryption_key")
    generate_encryption_key(encryption_key_file)
    tmp_encrypted_asset_path = os.path.join(tmp_files, "tmp_encrypted_result")
    SymmetricEncryption().encrypt_file(
        tmp_result_archive, encryption_key_file, tmp_encrypted_asset_path
    )
    os.remove(tmp_result_archive)

    # encrypt the encryption key with the public key provided
    public_key = os.getenv("RESULT_COLLECTOR")

    public_key_bytes = base64.b64decode(public_key)
    with open(encryption_key_file, "rb") as f:
        encryption_key_bytes = f.read()
    encrypted_key_bytes = AsymmetricEncryption().public_key_encrypt(
        public_key_bytes, encryption_key_bytes
    )
    os.remove(encryption_key_file)

    result_manager_instance = result_manager(result_config)
    result_manager_instance.initialize()
    result_manager_instance.write_result(tmp_encrypted_asset_path)
    result_manager_instance.write_key(encrypted_key_bytes)
    os.remove(tmp_encrypted_asset_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--result-files",
        required=True,
        help="Folder to read result files from",
    )

    args = parser.parse_args()
    store_results(args)
