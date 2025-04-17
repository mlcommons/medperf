# How to configure container build for your application

- (Explanation TBD)

# How to configure container for custom FL software

- (Explanation TBD)

# How to build

- Build the openfl base image:

```bash
git clone https://github.com/securefederatedai/openfl.git
cd openfl
git checkout e6f3f5fd4462307b2c9431184190167aa43d962f
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
