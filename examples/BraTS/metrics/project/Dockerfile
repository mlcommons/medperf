FROM cbica/captk:release-1.8.1

RUN yum install -y xz-devel

RUN cd /work/CaPTk/bin/ && \
    curl https://captk.projects.nitrc.org/Hausdorff95_linux.zip --output Hausdorff95_linux.zip && \
    unzip -o Hausdorff95_linux.zip && \
    chmod a+x Hausdorff95 && \
    rm Hausdorff95_linux.zip

ENV LANG C.UTF-8

# install all python requirements
RUN yum install python3.8 python3-pip -y
# FIXME this does not result in python 3.8 being installed. Any idea why?

WORKDIR /project
COPY ./requirements.txt ./requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

# copy all files
COPY ./ /project

ENTRYPOINT ["python3", "mlcube.py"]
