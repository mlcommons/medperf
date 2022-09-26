def cube_local_hashes_generator(valid=True, with_tarball=True, with_image=True):
    local_hashes = {"additional_files_tarball_hash": "", "image_tarball_hash": ""}

    if with_tarball:
        local_hashes["additional_files_tarball_hash"] = (
            "additional_files_tarball_hash" if valid else "incorrect_hash"
        )

    if with_image:
        local_hashes["image_tarball_hash"] = (
            "image_tarball_hash" if valid else "incorrect_hash"
        )

    return local_hashes
