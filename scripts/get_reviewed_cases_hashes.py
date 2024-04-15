import tarfile
import hashlib
import shutil
import os
import yaml


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


def main():
    dst = ".reviewed_cases_contents"
    hashes_file = "reviewed_cases_hashes.yaml"

    # Create destination folder
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(dst, exist_ok=True)

    # Extract contents
    with tarfile.open("reviewed_cases.tar.gz") as file:
        file.extractall(dst)

    # Get hashes of tree
    hash_dict = generate_hash_dict(dst)

    # Write results to a file
    with open(hashes_file, "w") as f:
        yaml.dump(hash_dict, f)

    # Delete generated files and folders
    shutil.rmtree(dst, ignore_errors=True)


if __name__ == "__main__":
    main()
