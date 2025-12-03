#! /bin/bash
mkdir tmp
cd tmp
git clone -b fets_2.0 https://github.com/FeTS-AI/Front-End.git
cd Front-End
git submodule update --init
docker build --target=fets_base -t local/fets_tool .
cd ../../
docker build --platform=linux/amd64 -t mlcommons/rano-data-prep-mlcube:1.0.10 .
rm -rf tmp