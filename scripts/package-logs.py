import os
from medperf import config
from medperf.init import initialize
import tarfile

def main():
    initialize()

    with tarfile.open("medperf_logs.tar.gz", "w:gz") as tar:
        tar.add(config.logs_folder, arcname=os.path.basename(config.logs_folder))

if __name__ == "__main__":
    main()