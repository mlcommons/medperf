# How to configure container build for your application

- List your pip requirements in `requirements.txt`
- List your software requirements in `Dockerfile`
- Modify the functions in `hooks.py` as needed. (Explanation TBD)

# How to configure container for custom FL software

- Change the base Docker image as needed.
- modify `aggregator.py` and `collaborator.py` as needed. Follow the implemented schema steps.

# How to build

- Build the container (use `-b` for building the base as well)

```bash
cd ..
bash build.sh
```

# NOTE

for local experiments, internal IP address or localhost will not work. Use internal fqdn.

# How to customize

TBD
