FROM andrewsu1/hemnet:latest
RUN rm -rf /HEMnet && git clone -b master --single-branch --depth 1 https://github.com/BiomedicalMachineLearning/HEMnet.git
COPY *.py /HEMnet/HEMnet/
WORKDIR "/HEMnet/HEMnet" 
ENV PATH="/opt/conda/envs/HEMnet/bin:$PATH"
CMD [ "/bin/bash" ]