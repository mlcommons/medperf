FROM local/openfl:local

ENV LANG C.UTF-8

COPY ./requirements.txt /mlcube_project/requirements.txt
RUN pip install --no-cache-dir -r /mlcube_project/requirements.txt

# Copy mlcube workspace
COPY . /mlcube_project

ENTRYPOINT ["python", "/mlcube_project/mlcube.py"]