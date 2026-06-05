from medperf import config
import os


class CustomWriter:
    """class to use with tqdm to print progress using config.ui"""

    def write(self, msg):
        config.ui.print(msg)

    def flush(self):
        pass


def get_file_size(file_object) -> int:
    """Get the size of a file in bytes."""
    try:
        total_bytes = os.fstat(file_object.fileno()).st_size
    except (AttributeError, OSError):
        total_bytes = None
    return total_bytes
