from medperf.tests.mocks.cube import TestCube
import os
from medperf import config


# TODO
def run_mlcube(mlcube_path, task, out_logs, params, port, env):
    c = TestCube()
    c.cube_path = os.path.join(mlcube_path, config.cube_filename)
    c.params_path = os.path.join(
        mlcube_path, config.workspace_path, config.params_filename
    )
    if config.platform == "singularity":
        c._set_image_hash_from_registry()
    c.run(task, out_logs, port=port, env_dict=env, **params)
