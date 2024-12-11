import os
import shutil
from tqdm import tqdm
from functools import reduce
from pathlib import Path
import hashlib

# Taken from https://code.activestate.com/recipes/577879-create-a-nested-dictionary-from-oswalk/
def get_directory_structure(rootdir):
    """
    Creates a nested dictionary that represents the folder structure of rootdir
    """
    dir = {}
    rootdir = rootdir.rstrip(os.sep)
    start = rootdir.rfind(os.sep) + 1
    for path, dirs, files in os.walk(rootdir):
        folders = path[start:].split(os.sep)
        subdir = dict.fromkeys(files)
        parent = reduce(dict.get, folders[:-1], dir)
        parent[folders[-1]] = subdir
    return dir


def has_prepared_folder_structure(data_path, labels_path) -> bool:
    data_struct = list(get_directory_structure(data_path).values())[0]
    labels_struct = list(get_directory_structure(labels_path).values())[0]
    
    expected_data_files = ["brain_t1c.nii.gz", "brain_t1n.nii.gz", "brain_t2f.nii.gz", "brain_t2w.nii.gz"]
    expected_labels_files = ["final_seg.nii.gz"]

    if "splits.csv" not in data_struct:
        return False

    for id in data_struct.keys():
        if data_struct[id] is None:
            # This is a file, ignore
            continue
        for tp in data_struct[id].keys():
            expected_subject_data_files = set(["_".join([id, tp, file]) for file in expected_data_files])
            expected_subject_labels_files = set(["_".join([id, tp, file]) for file in expected_labels_files])

            found_data_files = set(data_struct[id][tp].keys())
            found_labels_files = set(labels_struct[id][tp].keys())

            data_files_diff = len(expected_subject_data_files - found_data_files)
            labels_files_diff = len(expected_subject_labels_files - found_labels_files)
            if data_files_diff or labels_files_diff:
                return False

    # Passed all checks
    return True


def normalize_path(path: str) -> str:
    """Remove mlcube-specific components from the given path

    Args:
        path (str): mlcube path

    Returns:
        str: normalized path
    """
    # for this specific problem, we know that all paths start with `/mlcube_io*`
    # and that this pattern won't change, shrink or grow. We can therefore write a
    # simple, specific solution
    if path.startswith("/mlcube_io"):
        return path[12:]

    # In case the path has already been normalized
    return path

def unnormalize_path(path: str, parent: str) -> str:
    """Add back mlcube-specific components to the given path

    Args:
        path (str): normalized path

    Returns:
        str: mlcube-specific path
    """
    if path.startswith(os.path.sep):
        path = path[1:]
    return os.path.join(parent, path)

def update_row_with_dict(df, d, idx):
    for key in d.keys():
        df.loc[idx, key] = d.get(key)


def get_id_tp(index: str):
    return index.split("|")


def set_files_read_only(path):
    for root, dirs, files in os.walk(path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            os.chmod(file_path, 0o444)  # Set read-only permission for files

        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            set_files_read_only(
                dir_path
            )  # Recursively call the function for subdirectories


def cleanup_storage(remove_folders):
    for folder in remove_folders:
        shutil.rmtree(folder, ignore_errors=True)


def copy_files(src_dir, dest_dir):
    # Ensure the destination directory exists
    os.makedirs(dest_dir, exist_ok=True)

    # Iterate through the files in the source directory
    for filename in os.listdir(src_dir):
        src_file = os.path.join(src_dir, filename)
        dest_file = os.path.join(dest_dir, filename)

        # Check if the item is a file (not a directory)
        if os.path.isfile(src_file):
            shutil.copy2(src_file, dest_file)  # Copy the file


# Taken from https://stackoverflow.com/questions/24937495/how-can-i-calculate-a-hash-for-a-filesystem-directory-using-python
def md5_update_from_dir(directory, hash):
    assert Path(directory).is_dir()
    for path in sorted(Path(directory).iterdir(), key=lambda p: str(p).lower()):
        hash.update(path.name.encode())
        if path.is_file():
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash.update(chunk)
        elif path.is_dir():
            hash = md5_update_from_dir(path, hash)
    return hash


def md5_dir(directory):
    return md5_update_from_dir(directory, hashlib.md5()).hexdigest()


def md5_file(filepath):
    return hashlib.md5(open(filepath,'rb').read()).hexdigest()


class MockTqdm(tqdm):
    def __getattr__(self, attr):
        return lambda *args, **kwargs: None
