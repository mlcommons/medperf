from .utils import run_command
import os
from medperf.utils import generate_tmp_uid
from medperf import config


def decrypt_gpg_file(encrypted_file_path, decryption_key_file, output_path):
    gpg_decrypt_command = [
        "gpg",
        "--batch",
        "--decrypt",
        "--output",
        output_path,
        "--passphrase-file",
        decryption_key_file,
        encrypted_file_path,
    ]
    run_command(gpg_decrypt_command)


def create_secure_folder():
    folder_name = generate_tmp_uid()
    folder_path = os.path.join(config.decrypted_files_folder, folder_name)
    os.makedirs(folder_path, mode=0o700)
    return folder_path
