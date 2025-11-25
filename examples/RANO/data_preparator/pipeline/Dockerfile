FROM mlcommons/rano-data-prep-mlcube:1.0.10

COPY ./project /project
ENV WORKSPACE_DIRECTORY='/workspace'
ENTRYPOINT ["python", "/project/direct_stages.py"]
