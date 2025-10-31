from typing import Optional, Union
from medperf.entities.report import TestReport


class TestTestReport(TestReport):
    demo_dataset_url: Optional[str] = "url"
    demo_dataset_hash: Optional[str] = "hash"
    data_path: Optional[str] = None
    labels_path: Optional[str] = None
    prepared_data_hash: Optional[str] = None
    data_preparation_mlcube: Optional[Union[int, str]] = 1
    model: Union[int, str] = 2
    data_evaluator_mlcube: Union[int, str] = 3
    results: Optional[dict] = {"acc": 1}
