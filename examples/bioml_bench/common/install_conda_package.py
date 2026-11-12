"""Installs a Python package from a conda package (.conda) into a folder, for
packages that have no wheel for the image's platform but a conda-forge build.
The package's files are checked against a SHA-256 hash.
Usage: python3 install_conda_package.py <url> <sha256> <site-packages folder>
Needs the zstandard package."""

import hashlib
import io
import sys
import tarfile
import urllib.request
import zipfile

import zstandard

SITE_PACKAGES = "lib/python3.11/site-packages/"


def main():
    url, sha256, target = sys.argv[1:]
    with urllib.request.urlopen(url, timeout=300) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != sha256:
        sys.exit(f"{url} does not match its SHA-256 hash")

    with zipfile.ZipFile(io.BytesIO(data)) as package:
        [files] = [name for name in package.namelist() if name.startswith("pkg-")]
        tar_data = zstandard.ZstdDecompressor().stream_reader(package.open(files))
        with tarfile.open(fileobj=tar_data, mode="r|") as tar:
            for member in tar:
                if member.name.startswith(SITE_PACKAGES) and member.isfile():
                    member.name = member.name[len(SITE_PACKAGES):]
                    tar.extract(member, target, filter="data")
    print(f"Installed {url.rsplit('/', 1)[1]} into {target}")


if __name__ == "__main__":
    main()
