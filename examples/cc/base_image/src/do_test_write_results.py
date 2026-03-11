import os
import json
from assets.factory import result_manager
from crypto import AsymmetricEncryption
import base64


def do_test() -> None:

    # get configs from environment variables
    result_config_str = os.getenv("RESULT_CONFIG")
    result_config = json.loads(result_config_str)
    # encrypt the encryption key with the public key provided
    public_key = os.getenv("RESULT_COLLECTOR")
    public_key_bytes = base64.b64decode(public_key)

    test_data = AsymmetricEncryption().public_key_encrypt(public_key_bytes, b"test")

    result_manager_instance = result_manager(result_config)
    result_manager_instance.initialize()
    result_manager_instance.do_test(test_data)


if __name__ == "__main__":
    do_test()
