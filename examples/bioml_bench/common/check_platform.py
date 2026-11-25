"""Fails the build if a compiled file was installed for another CPU than the
image's: packages without a wheel for the target are built on the build
machine, for its CPU. Usage: python3 check_platform.py <folder> <amd64|arm64>"""

import sys
from pathlib import Path

ELF_MACHINES = {62: "amd64", 183: "arm64"}


def main():
    folder, target = sys.argv[1:]
    wrong = []
    for path in Path(folder).rglob("*.so*"):
        if not path.is_file():
            continue
        with open(path, "rb") as f:
            header = f.read(20)
        if header[:4] != b"\x7fELF":
            continue
        machine = ELF_MACHINES.get(int.from_bytes(header[18:20], "little"), "unknown")
        if machine != target:
            wrong.append(f"{path} ({machine})")
    if wrong:
        sys.exit(f"Compiled for another CPU than {target}:\n" + "\n".join(wrong))
    print(f"All compiled files are for {target}")


if __name__ == "__main__":
    main()
