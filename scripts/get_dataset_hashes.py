import hashlib
import os
import yaml

from medperf import config
from medperf.init import initialize
from typer import Option


def sha256sum(filename):
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(filename, "rb", buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()


def generate_hash_dict(path):
    hash_dict = {}
    contents = os.listdir(path)

    for item in contents:
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            hash_dict[item] = generate_hash_dict(item_path)
        else:
            hash_dict[item] = sha256sum(item_path)

    return hash_dict


def main(
    dataset_uid: str = Option(None, "-d", "--dataset"),
    output_file: str = Option("dataset_hashes.yaml", "-f", "--file"),
):
    initialize()
    dset_path = os.path.join(config.datasets_folder, dataset_uid)

    # Get hashes of tree
    hash_dict = generate_hash_dict(dset_path)

    # Write results to a file
    with open(output_file, "w") as f:
        yaml.dump(hash_dict, f)


if __name__ == "__main__":
    run(main)
