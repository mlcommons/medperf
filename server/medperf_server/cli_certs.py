import os
import shutil
import subprocess
from pathlib import Path


def ensure_cert(cert_file: str, key_file: str, regenerate: bool = False) -> None:
    """Generates a self-signed dev certificate unless one is already there.

    Regenerating invalidates any client that already trusts the old cert, so it
    only happens on explicit request.
    """
    if regenerate or not (os.path.isfile(cert_file) and os.path.isfile(key_file)):
        subprocess.run(
            [
                "openssl",
                "req",
                "-x509",
                "-nodes",
                "-days",
                "365",
                "-newkey",
                "rsa:3072",
                "-keyout",
                key_file,
                "-out",
                cert_file,
                "-subj",
                "/C=US/ST=Any/L=Any/O=MedPerf/CN=127.0.0.1",
                "-addext",
                "subjectAltName=DNS:localhost,IP:127.0.0.1",
            ],
            check=True,
        )

    # Also trusted by the medperf CLI's local/testauth profiles
    medperf_dev_dir = Path.home() / ".medperf_dev"
    os.makedirs(medperf_dev_dir, exist_ok=True)
    shutil.copy(cert_file, medperf_dev_dir / "cert.crt")
