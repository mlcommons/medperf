"""Checks the prepared connection is one the benchmark can actually run.

Shape only. Whether the service answers is not checked here: the preparation
container runs on the data owner's premises with no network, and the workload
checks it for real before it loads a model.
"""

import yaml

import connection


def perform_sanity_checks(data_path, labels_path, parameters):
    settings = connection.read(data_path, labels_path)

    for field in ("url", "key"):
        assert settings.get(field), f"The prepared connection has no {field}"

    url = str(settings["url"])
    assert url.startswith(("http://", "https://")), f"{url} is not an http(s) URL"

    shape = connection.read_run_shape(parameters)
    for field, expected in shape.items():
        assert settings.get(field) == expected, (
            f"{field} is {settings.get(field)!r}, but the parameters ask for {expected!r}"
        )

    print(
        f"Sanity checks ran successfully. {settings.get('benchmark_type', 'general')}"
        f" run, {settings.get('mode', 'test')} mode,"
        f" {settings.get('locale', 'en_us')}."
    )


if __name__ == "__main__":
    parameters_file = "/mlcommons/volumes/parameters/parameters_file.yaml"
    data_path = "/mlcommons/volumes/data"
    labels_path = "/mlcommons/volumes/labels"

    with open(parameters_file) as f:
        parameters = yaml.safe_load(f)

    perform_sanity_checks(data_path, labels_path, parameters)
