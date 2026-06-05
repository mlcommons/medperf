DATA_FROM_PREPARED_EXAMPLES = [
    {"model": 1, "evaluator": 2, "data_uid": 3},
    {"benchmark": 1, "data_uid": 3},
]

DATA_FROM_BENCHMARK_EXAMPLES = [
    {
        "model": 1,
        "evaluator": 2,
        "data_prep": 3,
        "benchmark": 1,
    },
    {
        "benchmark": 1,
    },
    {"benchmark": 1, "model": 1},
]

INVALID_EXAMPLES = [
    # missing data source
    {
        "model": 1,
        "evaluator": 2,
        "data_prep": 3,
    },
    # missing model
    {"evaluator": 2, "data_uid": 3},
    # missing evaluator
    {"model": 1, "data_uid": 3},
    # redundant benchmark
    {
        "model": 1,
        "evaluator": 2,
        "benchmark": 1,
        "data_prep": 3,
        "data_uid": 3,
    },
    # redundant prep cube
    {
        "model": 1,
        "evaluator": 2,
        "data_prep": 3,
        "data_uid": 3,
    },
]
