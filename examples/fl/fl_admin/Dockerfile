FROM local/openfl:local

ENV LANG C.UTF-8

COPY project/requirements.txt /project/requirements.txt
RUN pip install --no-cache-dir -r /project/requirements.txt

# Copy mlcube workspace
COPY project /project

ENTRYPOINT ["python", "/project/entrypoint.py"]