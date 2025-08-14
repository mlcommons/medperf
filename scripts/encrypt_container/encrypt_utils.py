from cryptography.fernet import Fernet


import os


def generate_fernet_key_and_encrypt(
        file_to_encrypt: os.PathLike,
        encrypted_image_output_path: os.PathLike
) -> tuple[bytes, Fernet]:
    key = Fernet.generate_key()
    fernet_obj = Fernet(key)

    with (
        open(file_to_encrypt, 'rb') as original,
        open(encrypted_image_output_path, 'wb') as encrypted
    ):
        encrypted_bytes = fernet_obj.encrypt(original.read())
        encrypted.write(encrypted_bytes)

    return key
