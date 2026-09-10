"""Turns a data owner's service connection into MedPerf's data/ + labels/ pair.

There is nothing to prepare in the usual sense: this benchmark has no prompts
on the premises. What this does is put the two halves of a run together --
the data owner's service and account, and the benchmark owner's run shape from
the preparation parameters -- and write them where the benchmark script looks.

Both output folders are written because MedPerf hashes the pair into the
dataset's identity. Point `medperf dataset submit -l` at the same folder as
`-d`; the labels folder is not read.
"""

import connection


def prepare_dataset(data_path, labels_path, parameters, output_path, output_labels_path):
    settings = connection.read_owner_settings(data_path)
    settings.update(connection.read_run_shape(parameters))

    connection.write(output_path, output_labels_path, settings)
    print(
        f"prepared a {settings.get('benchmark_type', 'general')} run"
        f" in {settings.get('mode', 'test')} mode"
        f" ({settings.get('locale', 'en_us')})"
    )


if __name__ == "__main__":
    import yaml

    parameters_file = "/mlcommons/volumes/parameters/parameters_file.yaml"
    data_path = "/mlcommons/volumes/raw_data"
    labels_path = "/mlcommons/volumes/raw_labels"
    output_path = "/mlcommons/volumes/data"
    output_labels_path = "/mlcommons/volumes/labels"

    with open(parameters_file) as f:
        parameters = yaml.safe_load(f)

    prepare_dataset(data_path, labels_path, parameters, output_path, output_labels_path)
