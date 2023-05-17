from medperf.utils import get_file_sha1


def calculate_fake_file_hash(fs, contents):
    # TODO: should calculate the hash of a string in memory
    fs.create_file("some_file", contents=contents)
    return get_file_sha1("some_file")
