FROM mlcommons/medperf-confidential-benchmark-base:0.0.0

ENV CUDA_VISIBLE_DEVICES="0"


# install project dependencies
RUN apt-get update && apt-get install --no-install-recommends -y git zlib1g-dev libffi-dev libgl1 libgtk2.0-dev gcc g++

RUN pip install torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2 --index-url https://download.pytorch.org/whl/cu121

COPY ./requirements.txt /project/requirements.txt

RUN pip install --no-cache-dir -r /project/requirements.txt

RUN git clone https://github.com/rachitsaluja/fets2-eval-LW
RUN cd fets2-eval-LW && git checkout e8ef3610ffa8afb29b3f3dc748c32d82869044b0
RUN sed -i '$s/scipy==.*/scipy==1.11.4/' fets2-eval-LW/requirements.txt
RUN sed -i 's/^connected_components_3d==.*/connected_components_3d==3.13.0/' fets2-eval-LW/requirements.txt
RUN pip install -r fets2-eval-LW/requirements.txt

# Copy project folder
COPY ./benchmark /project/benchmark
RUN mv /fets2-eval-LW/* /project/benchmark/metrics/
