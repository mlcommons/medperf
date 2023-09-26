# How this MLCube was created

1. Clone the GaNDLF fork/branch:

```bash
git clone https://github.com/rachitsaluja/GaNDLF.git
cd GaNDLF
git checkout c2a2c1cc6fc1d307a70068160066acdf1e8cd8bc
```

2. [Install GaNDLF from source](https://mlcommons.github.io/GaNDLF/setup/)
3. Go back to `setup` folder. Run:

```
bash
gandlf_deploy -t docker --mlcube-type metrics -r ./mlcube_template -o ../mlcube -e ./entrypoint.py
```
4. Cleanup:

```bash
rm -rf GaNDLF
```