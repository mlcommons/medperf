"""Shape, and nothing else.

These statistics travel to the MedPerf server as part of the dataset's report,
which the benchmark owner can read. For an ordinary dataset that is
unremarkable; here the dataset is a service and a key, so neither the key nor
anything that identifies the account may appear. The host is named because the
benchmark owner is entitled to know which service graded a run of their
benchmark.
"""

from urllib.parse import urlparse

import yaml

import connection


def generate_statistics(data_path, labels_path, parameters, out_path):
    settings = connection.read(data_path, labels_path)
    parsed = urlparse(str(settings.get("url", "")))

    statistics = {
        "service_scheme": parsed.scheme,
        "service_host": parsed.hostname or "",
        "benchmark_type": settings.get("benchmark_type", "general"),
        "mode": settings.get("mode", "test"),
        "locale": settings.get("locale", "en_us"),
        "num_prompts": 0,  # none are held here; the service has them
    }

    with open(out_path, "w") as f:
        yaml.safe_dump(statistics, f, sort_keys=False)


if __name__ == "__main__":
    parameters_file = "/mlcommons/volumes/parameters/parameters_file.yaml"
    data_path = "/mlcommons/volumes/data"
    labels_path = "/mlcommons/volumes/labels"
    output_path = "/mlcommons/volumes/statistics/statistics.yaml"

    with open(parameters_file) as f:
        parameters = yaml.safe_load(f)

    generate_statistics(data_path, labels_path, parameters, output_path)
