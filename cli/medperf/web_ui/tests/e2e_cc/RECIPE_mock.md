# Recipe — chest X-ray CC end to end, web UI, mock backend

Run MedPerf's confidential-computing workflow from first click to last through
the web UI, with the mock CC backends. Three parties, one benchmark, one
confidential execution, no cloud account.

**Done means:** the run prints `PASSED: 30 steps` (`PASSED: 33 steps` with
`-o modelowner`), and there is one `run.mp4` of the browser doing it.

Do the GCP version (`RECIPE_gcp.md`, beside this file) only after this one
passes. It is the same workflow and it is much cheaper to debug here.

## Parameters

`fix_problems` — given to you by whoever asked for the run.

- `False` — at the first thing that does not work, **stop**. Report the step,
  the command, the output, and which file and line you think is responsible.
  Change nothing.
- `True` — fix it, say plainly what you changed and why, then start the run
  again from the top. Never edit a test to make it pass, never delete a check to
  get past it, and never widen a timeout without saying you did.

Either way: report what actually happened. A step you skipped is a step you
report as skipped.

## Paths

`REPO` is the repository root — the directory holding `cli/` and `cc/`. `VENV`
is the virtualenv MedPerf is installed into. On the machine this was written
for:

```
REPO=/home/hasan_kassem/medperf_ws/medperf
VENV=/home/hasan_kassem/medperf_ws/venv
```

Everything below runs with `source $VENV/bin/activate` and `cd $REPO`.

If `medperf --version` does not work in that virtualenv, install the client and
the CC package into it — `pip install -e cc/ -e cli/` from `$REPO` — plus
`pip install -r server/requirements.txt -r cli/test-requirements.txt` for the
server and selenium. Chrome and docker have to be installed; selenium fetches
its own driver.

## 1. Check the codebase still matches this recipe

Do this first, every time. This recipe names files, flags and form fields; any
of them can have moved. Report anything that has, before running anything.

```bash
cd $REPO && git log --oneline -5 && git status --short
```

These must exist:

| file | what this recipe uses it for |
| --- | --- |
| `cli/webui_tests_cc.sh` | builds the environment, starts the web UI, runs the test |
| `cli/medperf/web_ui/tests/e2e_cc/webui_tests_cc.py` | the clicking |
| `cli/medperf/web_ui/tests/e2e_cc/recorder.py` | the display and the video |
| `cli/medperf/web_ui/tests/pages/cc/asset_cc_page.py` | the CC form on a model or dataset |
| `cli/medperf/web_ui/tests/pages/cc/settings_cc_page.py` | the CC forms on the settings page |
| `examples/cc/chestxray/implementation/container_config.yaml` | the benchmark script container |

Check these three:

- `webui_tests_cc.sh` still accepts `-p PORT`, `-H` and `-o OPERATOR`, and still
  exports `CC_DATA_PATH`, `CC_LABELS_PATH`, `CC_MODEL_TARBALL`,
  `WEBUI_ARTIFACTS`, `CC_OPERATOR`.
- `webui_tests_cc.py` still accepts `--port`, `--artifacts`, `--headed`,
  `--no-record`, `--fps`, and still ends with `PASSED: N steps`.
- The CC form fields the script fills still exist:

```bash
python -c "
from medperf_cc import asset_backends, runner_backends, result_store_backends
import json; print(json.dumps({'asset': asset_backends(), 'runner': runner_backends(),
                               'result_store': result_store_backends()}, indent=1))"
```

The `mock` backend must take `root` and nothing else, in all four places. If it
grew a setting, `CC_SETTINGS` in `webui_tests_cc.py` has to grow it too — that
is drift, report it.

## 2. Bring up the MedPerf server

The test needs a local MedPerf server with a **fresh database**. A container is
unique on its image, config and parameters, so a second run against the same
database is rejected when it submits the same preparation container. Reset it
every time.

```bash
source $VENV/bin/activate
cd $REPO/server
cp .env.local.local-auth .env
sh reset_db_postgresql.sh          # recreates the postgres container and migrates
```

Then start the server, unless one is already up on 8000:

```bash
cd $REPO/server
setsid nohup sh setup-dev-server.sh > /tmp/django.log 2>&1 < /dev/null &
```

It writes `server/cert.crt`, which is the certificate the client's `local`
profile trusts. Add `-g 0` to keep an existing one instead — worth doing if a
server is already running on it. Wait until this answers `401`:

```bash
curl -sk -o /dev/null -w '%{http_code}\n' https://localhost:8000/api/v0/benchmarks/
```

Do **not** seed the database. `seed.py` registers the same chest X-ray
preparation container this test submits, and the submission would be rejected.

## 3. Make sure it can record

The browser is given a virtual X display and ffmpeg records that display for
the whole run. Two things have to be there:

```bash
which Xvfb || sudo apt-get install -y xvfb
which ffmpeg || pip install imageio-ffmpeg
```

Without them the run still passes, headless, with no video at all — and it says
so on the first line. That is a failure of this recipe's goal; report it rather
than reporting a pass.

## 4. Run it

```bash
source $VENV/bin/activate
cd $REPO
sh cli/webui_tests_cc.sh -p 8200 2>&1 | tee /tmp/webui_cc.log
```

Takes about five minutes. It prints its test root on the first line; the
artifacts are under `<test root>/artifacts`.

It does all of this by itself: fetches the chest X-ray sample data and weights,
wipes `/tmp/medperf_cc_mock`, creates the three profiles, starts one web UI on
the given port, and drives the browser through:

benchmark owner submits the preparation container, the benchmark script
container, the reference weights and the benchmark → model owner submits the
weights under test, asks for an association, gets a certificate → data owner
gets a certificate, submits the dataset, prepares it, marks it operational, asks
for an association → benchmark owner approves both → model owner and data owner
each configure their asset for CC and sync its policy → data owner sets up where
results are received, the operator sets up the machine they run on → the
operator runs the benchmark → data owner submits the result.

`-H` runs it on your own screen and records nothing — for watching live, not
for producing the video.

### Both operator scenarios

Who *operates* is a separate question from who the results are for. Both
policies here release them to the data owner, so:

```bash
sh cli/webui_tests_cc.sh -p 8200                    # dataowner operates: 30 steps
sh cli/webui_tests_cc.sh -p 8200 -o modelowner      # modelowner operates: 33 steps
```

With `-o modelowner` the operator never sees the results — they are sealed for
the data owner's key. Three extra steps cover that: the model owner's page names
the execution they have to hand over, the data owner collects it by clicking
**Collect results** on their dataset page, and the ordinary **Submit** button
reports it. That is the half `medperf confidential download_cc_results` exists
for, and the only path where it is exercised.

Run both. They need a fresh database each — see section 2.

## 5. What you should have at the end

```
<test root>/artifacts/run.mp4        the browser, start to end
<test root>/webui.log                the web UI's own log
```

Check the video is real before reporting success — it should be about as long
as the run took:

```bash
ffmpeg -hide_banner -i <test root>/artifacts/run.mp4 2>&1 | grep -E 'Duration|Stream'
```

(If `ffmpeg` is not on `PATH`, the bundled one is
`python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"`.)

The recording is real time, so five minutes of run is five minutes of video. If
that is more than whoever asked wants to sit through:

```bash
ffmpeg -i run.mp4 -filter:v setpts=PTS/4 -an run_4x.mp4
```

Then give the person the path to `run.mp4` and the step count.

Failure screenshots (`<step>.png`, `<step>.html`) only appear when a step fails.
If they are there, the run did not pass, whatever else it printed.

## 6. When something fails

The script prints the failing step, the browser's URL, a screenshot and the
page's HTML, and then the last 40 lines of the web UI log. Read those first —
in that order. The video ends on the failure with the step name in the caption
bar, which is usually the quickest way to see what the browser was looking at.

Things that have actually gone wrong here:

| symptom | cause |
| --- | --- |
| every step fails at the login page | the MedPerf server is not up, or its database was not reset |
| `task did not finish within 1800s` | a task is waiting on a second prompt the script did not answer, or docker is not running |
| the first container submission fails | the database already has that container — reset it |
| the run step fails with a docker error | the mock runner needs docker; check `docker version` |
| `Not recording: Xvfb is not installed` | step 3 |
| no `run.mp4` and no message | ffmpeg died; its error is printed where the video path would have been |

With `fix_problems=False`, stop at the first one and report. With `True`, fix
and start again from step 2 — a half-finished run leaves entities on the server
that make the next one fail differently.

## 7. Clean up

```bash
docker ps -aq --filter name=medperf-cc-mock- | xargs -r docker rm -f
rm -rf /tmp/medperf_cc_mock
```

Keep the test root that has the video in it. Old ones can go:

```bash
ls -d /tmp/medperf_webui_cc_*
```

Leave the postgres container and the server running if more runs are coming.
