import re


def import_external_python_function(function_path: str):
    import importlib

    condition_module, condition_function = function_path.rsplit(".", maxsplit=1)
    imported_module = importlib.import_module(condition_module)
    function_obj = getattr(imported_module, condition_function)

    return function_obj


def create_legal_dag_id(subject_slash_timepoint, replace_char="_"):
    legal_chars = "A-Za-z0-9_-"
    legal_id = re.sub(rf"[^{legal_chars}]", replace_char, subject_slash_timepoint)
    return legal_id
