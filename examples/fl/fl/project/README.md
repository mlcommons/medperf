# How to configure container build for your application

- List your pip requirements in `requirements.txt`
- List your software requirements in `Dockerfile`
- Modify the functions in `hooks.py` as needed. (Explanation TBD)

# How to configure container for custom FL software

- Change the base Docker image as needed.
- modify `aggregator.py` and `collaborator.py` as needed. Follow the implemented schema steps.

# How to build

- Build the openfl base image:

```bash
git clone https://github.com/securefederatedai/openfl.git
git checkout e6f3f5fd4462307b2c9431184190167aa43d962f
cd openfl
docker build -t local/openfl:local -f openfl-docker/Dockerfile.base .
cd ..
rm -rf openfl
```

- Build the MLCube

```bash
cd ..
bash build.sh
```

# NOTE

for local experiments, internal IP address or localhost will not work. Use internal fqdn.

# How to customize

TBD
