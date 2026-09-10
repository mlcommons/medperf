"""Where the run happens: the benchmark service, and the account reaching it.

There is no prompt set on this machine. The prompts belong to the service, and
so do the annotators and the grades -- this container answers prompts and
nothing else. What the data owner registers as a MedPerf dataset is therefore
not data: it is the connection that reaches theirs.

`prep/` writes this file into `data/`; this reads it back. The filename and the
keys are the contract between the two containers, and changing one without the
other is the failure this module exists to make obvious.
"""

import os
from dataclasses import dataclass

import yaml

FILENAME = "connection.yaml"

REQUIRED = ("url", "key")

# Lowercased, because the service compares them as literals.
NORMALISED = {"benchmark_type": "general", "mode": "test", "locale": "en_us"}


@dataclass(frozen=True)
class Connection:
    url: str
    key: str
    benchmark_type: str
    mode: str
    locale: str
    model_id: str


def read(data_path: str) -> Connection:
    path = os.path.join(data_path, FILENAME)
    if not os.path.exists(path):
        raise RuntimeError(
            f"No {FILENAME} under {data_path}. The dataset for this benchmark is"
            " the connection to the benchmark service -- see prep/."
        )
    with open(path) as f:
        described = yaml.safe_load(f) or {}

    missing = [field for field in REQUIRED if not described.get(field)]
    if missing:
        raise RuntimeError(f"{path} is missing {', '.join(missing)}")

    return Connection(
        url=str(described["url"]).strip(),
        key=str(described["key"]).strip(),
        model_id=str(described.get("model_id") or "medperf-sut").strip(),
        **{
            field: str(described.get(field) or default).strip().lower()
            for field, default in NORMALISED.items()
        },
    )
