from medperf.tests.mocks.cube import TestCube
import os
from medperf import config


def run_mlcube(mlcube_path, task, out_logs, params, port, env):
    c = TestCube()
    c.path = mlcube_path
    c.cube_path = os.path.join(c.path, config.cube_filename)
    c.params_path = os.path.join(c.path, config.params_filename)
    c.run(task, out_logs, port=port, env_dict=env, **params)
