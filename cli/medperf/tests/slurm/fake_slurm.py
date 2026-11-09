# A tiny stand-in for Slurm's sbatch/squeue/sacct/scancel, for integration tests.
#
# It is invoked as `python fake_slurm.py <command> <args...>` by wrapper scripts
# named after the Slurm commands. `sbatch` runs the job script immediately as a
# detached background process (honouring --output and --chdir); the other commands
# read the job's state from FAKE_SLURM_STATE.
#
# Only what MedPerf's launcher needs is imitated (plus `--wrap`): there is no queue,
# no resource enforcement, and squeue/sacct ignore format options.
#
# Behaviour switches (environment variables):
#     FAKE_SLURM_REJECT=1     sbatch rejects every submission
#     FAKE_SLURM_NO_SACCT=1   sacct reports that accounting is disabled
#     FAKE_SLURM_PURGE=1      squeue forgets finished jobs immediately
#     FAKE_SLURM_CLUSTER=x    sbatch --parsable prints "<id>;x"

import os
import signal
import subprocess
import sys

STATE = os.environ["FAKE_SLURM_STATE"]


def job_path(job_id, name):
    return os.path.join(STATE, job_id, name)


def read(job_id, name):
    try:
        with open(job_path(job_id, name)) as f:
            return f.read().strip()
    except OSError:
        return None


def option(args, name):
    for arg in args:
        if arg.startswith(f"--{name}="):
            return arg.split("=", 1)[1]
    return None


def job_id_arg(args):
    value = option(args, "jobs")
    for flag in ("-j", "--jobs"):
        if value is None and flag in args:
            value = args[args.index(flag) + 1]
    if value is None:
        value = [a for a in args if not a.startswith("-")][-1]
    return value


def state_of(job_id):
    if not os.path.isdir(os.path.join(STATE, job_id)):
        return None
    if read(job_id, "cancelled"):
        return "CANCELLED"
    rc = read(job_id, "rc")
    if rc is None:
        return "RUNNING"
    return "COMPLETED" if rc == "0" else "FAILED"


def sbatch(args):
    if os.environ.get("FAKE_SLURM_REJECT"):
        print(
            "sbatch: error: Batch job submission failed: "
            "Invalid account or account/partition combination specified",
            file=sys.stderr,
        )
        return 1
    counter = os.path.join(STATE, "counter")
    job_id = str(int(open(counter).read()) + 1) if os.path.exists(counter) else "1000"
    with open(counter, "w") as f:
        f.write(job_id)
    os.makedirs(os.path.join(STATE, job_id))
    with open(job_path(job_id, "argv"), "w") as f:
        f.write("\n".join(args))

    wrap = option(args, "wrap")
    if wrap is None and "--wrap" in args:
        wrap = args[args.index("--wrap") + 1]
    if wrap is not None:
        script = job_path(job_id, "wrap.sh")
        with open(script, "w") as f:
            f.write(f"#!/bin/bash\n{wrap}\n")
    else:
        script = args[-1]
    directives = []
    with open(script) as f:
        for line in f:
            if line.startswith("#SBATCH "):
                directives.append(line[len("#SBATCH "):].strip())

    # command-line options override directives, as in real sbatch
    output = option(args, "output") or option(directives, "output") or "slurm-%j.out"
    output = output.replace("%j", job_id)
    chdir = option(directives, "chdir") or os.getcwd()
    rc_file = job_path(job_id, "rc")
    log = open(output, "a")
    proc = subprocess.Popen(
        ["bash", "-c", 'bash "$1"; echo $? > "$2"', "job", script, rc_file],
        stdout=log,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        cwd=chdir,
        env={**os.environ, "SLURM_JOB_ID": job_id},
        start_new_session=True,
    )
    with open(job_path(job_id, "pid"), "w") as f:
        f.write(str(proc.pid))
    cluster = os.environ.get("FAKE_SLURM_CLUSTER")
    print(f"{job_id};{cluster}" if cluster else job_id)
    return 0


def squeue(args):
    job_id = job_id_arg(args)
    state = state_of(job_id)
    finished = state not in (None, "RUNNING")
    if state is None or (finished and os.environ.get("FAKE_SLURM_PURGE")):
        print("slurm_load_jobs error: Invalid job id specified", file=sys.stderr)
        return 1
    print(f"{state}|None|fakenode01")
    return 0


def sacct(args):
    if os.environ.get("FAKE_SLURM_NO_SACCT"):
        print("sacct: error: Slurm accounting storage is disabled", file=sys.stderr)
        return 1
    job_id = job_id_arg(args)
    state = state_of(job_id)
    if state is not None:
        rc = read(job_id, "rc") or "0"
        print(f"{job_id}|{state}|{rc}:0|fakenode01")
    return 0


def scancel(args):
    job_id = job_id_arg(args)
    state = state_of(job_id)
    if state != "RUNNING":
        print(f"scancel: error: Kill job error on job id {job_id}", file=sys.stderr)
        return 1
    with open(job_path(job_id, "cancelled"), "w") as f:
        f.write("1")
    try:
        os.killpg(int(read(job_id, "pid")), signal.SIGTERM)
    except ProcessLookupError:
        pass
    return 0


if __name__ == "__main__":
    command = sys.argv[1]
    handlers = {"sbatch": sbatch, "squeue": squeue, "sacct": sacct, "scancel": scancel}
    if command not in handlers:
        sys.exit(f"fake_slurm: unknown command {command}")
    sys.exit(handlers[command](sys.argv[2:]))
