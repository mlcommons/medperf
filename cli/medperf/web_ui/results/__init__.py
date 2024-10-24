from pathlib import Path
from typing import Dict

from medperf import config
from medperf.account_management import get_medperf_user_data
from medperf.entities.result import Result

results: Dict[str, Result] = {}


def fetch_all_results() -> None:
    for result_dir in Path(Result.get_storage_path()).iterdir():
        result_id = result_dir.name
        if result_dir.is_dir():
            try:
                if result_id.isdigit():
                    result_id = int(result_id)
                # Retrieve the result using the result ID
                result = Result.get(result_id)
                result_str_bmd_name = result.local_id
                results[result_str_bmd_name] = result
            except Exception as e:
                config.ui.print_error(f"Error retrieving result for {result_id}: {e}")

    for result in Result.all(
        filters={"owner": get_medperf_user_data()["id"]}
    ):
        result_str_bmd_name = result.local_id
        results[result_str_bmd_name] = result

