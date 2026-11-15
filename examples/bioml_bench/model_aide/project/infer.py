"""Runs BioML-bench's AIDE agent on a prepared task, as BioML-bench's
agents/aide/start.sh does, with the LLM served by vLLM inside the container.

1. Starts vLLM on localhost with the LLM's weights from the additional files.
2. Writes the agent's instructions: BioML-bench's general instructions, AIDE's
   notes (hardware, time and step limits) and the task's description.md.
3. Runs AIDE within the time limit. AIDE keeps the submission of its best
   solution so far, so a run stopped at the time limit still has one.
4. Writes that submission and the agent's logs to the predictions folder.
"""

import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import yaml

DATA_PATH = "/mlcommons/volumes/data"
PARAMETERS_PATH = "/mlcommons/volumes/parameters/parameters_file.yaml"
ADDITIONAL_FILES_PATH = "/mlcommons/volumes/additional_files"
PREDICTIONS_PATH = Path("/mlcommons/volumes/predictions")
PROJECT_PATH = Path(__file__).parent
# /tmp is the only writable folder when MedPerf runs the container
WORK_PATH = Path("/tmp/aide")
EXPERIMENT = "bioml"
LLM_URL = "http://127.0.0.1:8000"
# For testing this container without a GPU only: use an OpenAI-compatible
# server already running at this URL instead of starting vLLM
TEST_LLM_URL = os.environ.get("BIOML_AGENT_TEST_LLM_URL")


def container_env():
    env = dict(os.environ)
    env.update(
        HOME="/tmp/home",
        XDG_CACHE_HOME="/tmp/cache",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        VLLM_NO_USAGE_STATS="1",
        DO_NOT_TRACK="1",
        # clusters often set a proxy, which must not be used for localhost
        NO_PROXY="127.0.0.1,localhost",
        no_proxy="127.0.0.1,localhost",
    )
    return env


def log_tail(path, lines=50):
    with open(path, errors="replace") as f:
        return "".join(f.readlines()[-lines:])


def start_llm_server(llm, env, log_path):
    weights = os.path.join(ADDITIONAL_FILES_PATH, llm["weights"])
    if not os.path.isdir(weights):
        raise FileNotFoundError(f"LLM weights not found: {weights}. They must be in the model's additional files")
    command = [
        "vllm", "serve", weights,
        "--served-model-name", llm["served_name"],
        "--host", "127.0.0.1",
        "--port", LLM_URL.rsplit(":", 1)[1],
        "--max-model-len", str(llm["max_model_len"]),
        "--gpu-memory-utilization", str(llm["gpu_memory_utilization"]),
        *llm.get("extra_args", []),
    ]
    print("Starting the LLM server:", " ".join(command), flush=True)
    # vLLM only: see vllm_shims/torchcodec
    shims = str(PROJECT_PATH / "vllm_shims")
    env = dict(env, PYTHONPATH=os.pathsep.join(filter(None, [shims, env.get("PYTHONPATH")])))
    with open(log_path, "w") as log:
        return subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)


def wait_for_llm_server(server, log_path, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if server.poll() is not None:
            raise RuntimeError(f"The LLM server exited with code {server.returncode}:\n{log_tail(log_path)}")
        try:
            with urllib.request.urlopen(f"{LLM_URL}/health", timeout=5) as response:
                if response.status == 200:
                    print("The LLM server is ready", flush=True)
                    return
        except OSError:
            pass
        time.sleep(10)
    raise TimeoutError(f"The LLM server was not ready after {timeout} s:\n{log_tail(log_path)}")


def stop(process, grace=30):
    if process.poll() is not None:
        return
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(grace)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def format_time(seconds):
    return f"{seconds // 3600}hrs {(seconds % 3600) // 60}mins {seconds % 60}secs"


def write_instructions(aide, path):
    # agent code runs on the CPUs: the container's GPUs serve the LLM
    hardware = f"{len(os.sched_getaffinity(0))} CPUs (no GPU: the GPU runs the LLM)"
    notes = (PROJECT_PATH / "additional_notes.txt").read_text().format(
        hardware=hardware, time_limit=format_time(aide["time_limit"]), steps=aide["steps"]
    )
    description = Path(DATA_PATH, "description.md").read_text()
    instructions = (PROJECT_PATH / "instructions.txt").read_text()
    path.write_text(f"{instructions}\n{notes}\nCOMPETITION INSTRUCTIONS\n------\n\n{description}")


def run_aide(llm, aide, env):
    instructions = WORK_PATH / "full_instructions.txt"
    write_instructions(aide, instructions)
    command = [
        sys.executable, str(PROJECT_PATH / "run_aide.py"),
        f"data_dir={DATA_PATH}",
        f"desc_file={instructions}",
        f"log_dir={WORK_PATH / 'logs'}",
        f"workspace_dir={WORK_PATH / 'workspaces'}",
        f"exp_name={EXPERIMENT}",
        f"agent.code.model={llm['served_name']}",
        f"agent.feedback.model={llm['served_name']}",
        f"agent.code.temp={aide['temperature']}",
        f"agent.feedback.temp={aide['temperature']}",
        f"agent.steps={aide['steps']}",
        f"agent.time_limit={aide['time_limit']}",
        f"exec.timeout={aide['exec_timeout']}",
    ]
    env = dict(env, OPENAI_BASE_URL=f"{TEST_LLM_URL or LLM_URL}/v1", OPENAI_API_KEY="local")
    agent = subprocess.Popen(command, env=env, cwd=WORK_PATH, start_new_session=True)
    try:
        agent.wait(aide["time_limit"])
        print(f"AIDE exited with code {agent.returncode}", flush=True)
    except subprocess.TimeoutExpired:
        print(f"Timed out after {format_time(aide['time_limit'])}", flush=True)
    finally:
        stop(agent)


def save_outputs(llm_log):
    workspace = WORK_PATH / "workspaces" / EXPERIMENT
    submission = workspace / "best_submission" / "submission.csv"
    if submission.exists():
        shutil.copy(submission, PREDICTIONS_PATH / "submission.csv")
        print("Saved the best solution's submission.csv", flush=True)
    else:
        print("AIDE found no working solution: there is no submission", flush=True)

    logs = PREDICTIONS_PATH / "agent_logs"
    logs.mkdir(exist_ok=True)
    for path in [
        workspace / "best_solution" / "solution.py",
        WORK_PATH / "logs" / EXPERIMENT / "aide.log",
        WORK_PATH / "logs" / EXPERIMENT / "journal.json",
        llm_log,
    ]:
        if path.exists():
            shutil.copy(path, logs / path.name)


def main():
    with open(PARAMETERS_PATH) as f:
        parameters = yaml.safe_load(f)
    llm, aide = parameters["llm"], parameters["aide"]
    WORK_PATH.mkdir(parents=True, exist_ok=True)
    env = container_env()
    llm_log = WORK_PATH / "vllm.log"

    server = None
    if TEST_LLM_URL:
        print(f"Testing: using the LLM server at {TEST_LLM_URL}", flush=True)
    else:
        server = start_llm_server(llm, env, llm_log)
    try:
        if server:
            wait_for_llm_server(server, llm_log, llm["startup_timeout"])
        run_aide(llm, aide, env)
    finally:
        if server:
            stop(server)
        save_outputs(llm_log)


if __name__ == "__main__":
    main()
