# How to run tests (see next section for a detailed guide)

- Run `setup_test_no_docker.sh` just once to create certs and download required data.
- Run `test.sh` to start the aggregator and three collaborators.
- Run `clean.sh` to be able to rerun `test.sh` freshly.
- Run `setup_clean.sh` to clear what has been generated in step 1.

## Detailed Guide

- Go to your medperf repo and checkout the required branch.
- Have medperf virtual environment activated (and medperf installed)
- run: `setup_test_no_docker.sh` to setup the test (you should `setup_clean.sh` if you already ran this before you run it again).
- run: `test.sh --d1 absolute_path --l2 absolute_path ...` to run the test
  - data paths can be specified in the command. --dn is for data path of collaborator n, --ln is for labels_path of collaborator n.
  - make sure gpu IDs are set as expected in `test.sh` script.
- to stop: `CTRL+C` in the terminal where you ran `test.sh`, then, `docker container ls`, then take the container IDs, then `docker container stop <ID>`, to stop relevant running containers (to identify containers to stop, they should have an IMAGE field same name as the one configured in docker image field in `mlcube.yaml`). You can at the end use `docker container prune` to delete all stopped containers if you want (not necessary).
- To rerun: you should first run `sh clean.sh`, then `sh test.sh` again.

## What to do when you want to

- change port: either change `setup_test_no_docker.sh` then clean setup and run setup again, or, go to `mlcube_agg/workspace/aggregator_config.yaml` and modify the file directly.
- Change address: change `setup_test_no_docker.sh` then clean setup and run setup again. (since the cert needs to be generated)
- change training_config: modify `mlcube/workspace/training_config.yaml` then run `sync.sh`.
- use custom data paths: pass data paths when running `test.sh` (`--d1, --d2, --l1, ...`)
- change weights: modify `mlcube/workspace/additional_files` then run `sync.sh`.
- fl_admin? connect to container and run fx commands. make sure a colab is an admin (to be detailed later)

- to use three collaborators instead of two:
  - go to `mlcube_agg/workspace/cols.yaml` and modify the list by adding col3.
  - in `test.sh`, uncomment col3's run command.

## to rebuild

sh build.sh (or with -b if you want to rebuild the openfl base as well. Configure `build.sh` to change how openfl base is built)
