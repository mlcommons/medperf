This is merely a toy example to demonstrate MedPerf's capabilities of running Encrypted Containers.
This the `container_config.yaml` file in this directory points to an encrypted form of the container found in the `../model_custom_cnn` directory.
The key to decrypt this container is also available right in this subdirectory as the `key.bin` file, so it's not really secret.

This key is to be used with the Fernet class of the `cryptography` Python library. It should be loaded as bytes (i.e use mode `rb` when opening and read all file contents, then use those bytes as the key)