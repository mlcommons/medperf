# How this MLCube was created

It's build like other basic MLCubes, but with one extra step first.

1. Clone the Front-End branch:

```bash
git clone https://github.com/FeTS-AI/Front-End.git
cd Front-End
git checkout 25eb0ca25933b79df0a274e79c5ed1336a20a92a
git module sync
git -c protocol.version=2 submodule update --init --force --depth=1
```

2. Build the FeTS tool docker image and tag it with `local/fets-tool:1.0.3`:

```bash
docker build -t local/fets-tool:1.0.3 .
```

3. Cleanup:

```bash
cd ..
rm -rf Front-End
```

4. Proceed to build the MLCube as normal:

```bash
cd ../mlcube
mlcube configure -Pdocker.build_strategy=always
```