import subprocess
import time


def _container_state(name: str) -> str:
    """Returns 'running', 'stopped', or 'absent'."""
    result = subprocess.run(
        ["docker", "container", "inspect", "-f", "{{.State.Running}}", name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return "absent"
    return "running" if result.stdout.strip() == "true" else "stopped"


def start_new_container(name: str) -> None:
    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            name,
            "-p",
            "127.0.0.1:5432:5432",
            "-e",
            "POSTGRES_USER=devuser",
            "-e",
            "POSTGRES_PASSWORD=devpassword",
            "-e",
            "POSTGRES_DB=devdb",
            "postgres:14.10-alpine3.17",
        ],
        check=True,
    )


def ensure_running(name: str) -> bool:
    """Starts the dev postgres container if it isn't already running.
    Never destroys an existing container. Returns True if it just started
    a fresh container (i.e. the caller should wait for it to come up)."""
    state = _container_state(name)
    if state == "running":
        return False
    if state == "stopped":
        subprocess.run(["docker", "start", name], check=True)
        return True
    start_new_container(name)
    return True


def recreate_container(name: str) -> None:
    """Stops and removes the container if it exists, then starts a fresh one."""
    for args in (
        ["docker", "container", "stop", name],
        ["docker", "container", "rm", name],
    ):
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"warning: {' '.join(args)} failed: {result.stderr.strip()}")
    start_new_container(name)


def wait_for_postgres(name: str, timeout: int = 60) -> None:
    """Blocks until the container accepts connections, or raises on timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = subprocess.run(
            ["docker", "exec", name, "pg_isready", "-U", "devuser", "-d", "devdb"],
            capture_output=True,
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError(f"Postgres container '{name}' was not ready after {timeout}s")
