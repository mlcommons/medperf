FROM smallstep/step-cli:0.26.1

RUN apt-get update && apt-get install jq-y

COPY . /mlcube_project

ENTRYPOINT ["/bin/bash"]
