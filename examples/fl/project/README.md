# How to configure container build

- List your pip requirements in `openfl_workspace/requirements.txt`
- Modify container base image and/or how GaNDLF is installed in `dockerfile` to have GPU support.
- Modify the GaNDLF hash (or simply copy your customized GaNDLF repo code) in `dockerfile` to use a custom GaNDLF version.

Note: the plan to be attached to the container should be GaNDLF+OpenFL plan (I guess).

# How to build

- Build the openfl base image:

```bash
git clone https://github.com/securefederatedai/openfl.git
git checkout 11db12785c1a6a2d3c75656b38108443f88919e8
cd openfl
docker build -t local/openfl:local -f openfl-docker/Dockerfile.base .
cd ..
rm -rf openfl
```

- Build the MLCube

```bash
cd ../mlcube
mlcube configure -Pdocker.build_strategy=always
```

# Expected assets to be attached

(outdated)

- cert folders: certificates of the aggregator/collaborator and the CA's public key
- collaborator list, FL plan, and the init weights for the aggregator
- training data for the collaborator

# NOTE

for local experiments, internal IP address or localhost will not work. Use internal fqdn.

# For later

- To use a plan that doesn't depend on GaNDLF, maybe `openfl_workspace/src` should be prepopulated with the necessary code.
