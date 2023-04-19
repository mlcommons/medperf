DATA_FROM_PATH_EXAMPLES = [
    {
        "model": 1,
        "evaluator": 2,
        "data_prep": 3,
        "data_path": "path",
        "labels_path": "path",
    },
    {"benchmark": 1, "data_path": "path", "labels_path": "path",},
]

DATA_FROM_DEMO_EXAMPLES = [
    {
        "model": 1,
        "evaluator": 2,
        "data_prep": 3,
        "demo_dataset_url": "url",
        "demo_dataset_hash": "hash",
    },
    {"benchmark": 1, "demo_dataset_url": "url", "demo_dataset_hash": "hash",},
]

DATA_FROM_PREPARED_EXAMPLES = [
    {"model": 1, "evaluator": 2, "data_uid": 3},
    {"benchmark": 1, "data_uid": 3},
]

DATA_FROM_BENCHMARK_EXAMPLES = [
    {"model": 1, "evaluator": 2, "data_prep": 3, "benchmark": 1,},
    {"benchmark": 1,},
    {"benchmark": 1, "model": 1},
]

INVALID_EXAMPLES = [
    # missing labelspath
    {"model": 1, "evaluator": 2, "data_prep": 3, "data_path": "path",},
    # missing demo hash
    {"model": 1, "evaluator": 2, "data_prep": 3, "demo_dataset_url": "url",},
    # missing data source
    {"model": 1, "evaluator": 2, "data_prep": 3,},
    # missing data prep
    {"model": 1, "evaluator": 2, "data_path": "path", "labels_path": "path",},
    {
        "model": 1,
        "evaluator": 2,
        "demo_dataset_url": "url",
        "demo_dataset_hash": "hash",
    },
    # missing model
    {
        "evaluator": 2,
        "data_prep": 3,
        "demo_dataset_url": "url",
        "demo_dataset_hash": "hash",
    },
    # missing evaluator
    {
        "model": 1,
        "data_prep": 3,
        "demo_dataset_url": "url",
        "demo_dataset_hash": "hash",
    },
    # redundant benchmark
    {
        "model": 1,
        "evaluator": 2,
        "benchmark": 1,
        "data_prep": 3,
        "data_path": "path",
        "labels_path": "path",
    },
    {
        "model": 1,
        "evaluator": 2,
        "benchmark": 1,
        "data_prep": 3,
        "demo_dataset_url": "url",
        "demo_dataset_hash": "hash",
    },
    # redundant prep cube
    {"model": 1, "evaluator": 2, "data_prep": 3, "data_uid": 3},
    # multiple data sources
    {
        "model": 1,
        "evaluator": 2,
        "data_prep": 3,
        "data_uid": 3,
        "data_path": "path",
        "labels_path": "path",
    },
    {
        "model": 1,
        "evaluator": 2,
        "data_prep": 3,
        "demo_dataset_url": "url",
        "data_path": "path",
        "labels_path": "path",
    },
    {
        "model": 1,
        "evaluator": 2,
        "data_prep": 3,
        "demo_dataset_url": "url",
        "demo_dataset_hash": "hash",
        "data_uid": 3,
    },
]
