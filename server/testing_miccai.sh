# TODO: remove me from the repo

# First, run the local server
# cd ~/medperf/server
# sh setup-dev-server.sh
# go to another terminal

cd ..
# # TODO: reset
# bash reset_db.sh
# sudo rm -rf keys
# sudo rm -rf ~/.medperf

# TODO: seed
# python seed.py --demo benchmark

# TODO: download data
# wget https://storage.googleapis.com/medperf-storage/testfl/data/col1.tar.gz
# tar -xf col1.tar.gz
# wget https://storage.googleapis.com/medperf-storage/testfl/data/col2.tar.gz
# tar -xf col2.tar.gz
# wget https://storage.googleapis.com/medperf-storage/testfl/data/test.tar.gz
# tar -xf test.tar.gz
# rm col1.tar.gz
# rm col2.tar.gz
# rm test.tar.gz

# TODO: activate local profile
# medperf profile activate local

# login
medperf auth login -e modelowner@example.com

# register prep mlcube
medperf mlcube submit -n prep \
    -m https://storage.googleapis.com/medperf-storage/testfl/mlcube_prep.yaml

# register training mlcube
medperf mlcube submit -n testfl \
    -m https://storage.googleapis.com/medperf-storage/testfl/mlcube-cpu.yaml?v=2 \
    -p https://storage.googleapis.com/medperf-storage/testfl/parameters-miccai.yaml \
    -a https://storage.googleapis.com/medperf-storage/testfl/init_weights_miccai.tar.gz

# register training exp
medperf training submit -n testtrain -d testtrain -p 1 -m 2

# mark as approved
bash admin_training_approval.sh

# register aggregator
medperf aggregator submit -n testagg -a $(hostname --fqdn) -p 50273

# associate aggregator
medperf aggregator associate -a 1 -t 1 -y


# register dataset
medperf auth login -e traincol1@example.com
medperf dataset create -p 1 -d datasets/col1 -l datasets/col1 --name col1 --description col1data --location col1location
medperf dataset submit -d $(medperf dataset ls | grep col1 | tr -s " " | cut -d " " -f 1) -y

# associate dataset
medperf training associate_dataset -t 1 -d 1 -y

# shortcut
bash shortcut.sh

# approve associations
medperf auth login -e modelowner@example.com
medperf training approve_association -t 1 -d 1
medperf training approve_association -t 1 -d 2

# lock experiment
medperf training lock -t 1

# # start aggregator
gnome-terminal -- bash -c "medperf aggregator start -a 1 -t 1; bash"

sleep 5

# # start collaborator 1
medperf auth login -e traincol1@example.com
gnome-terminal -- bash -c "medperf training run -d 1 -t 1; bash"

sleep 5

# # start collaborator 2
medperf auth login -e traincol2@example.com
medperf training run -d 2 -t 1


############### eval starts


# submit reference model
medperf auth login -e benchmarkowner@example.com
medperf mlcube submit -n refmodel \
    -m https://storage.googleapis.com/medperf-storage/testfl/mlcube_other.yaml

# submit metrics mlcube
medperf mlcube submit -n metrics \
    -m https://storage.googleapis.com/medperf-storage/testfl/mlcube_metrics.yaml \
    -p https://storage.googleapis.com/medperf-storage/testfl/parameters_metrics.yaml

# submit benchmark metadata
medperf benchmark submit --name pathmnistbmk --description pathmnistbmk \
    --demo-url https://storage.googleapis.com/medperf-storage/testfl/data/sample.tar.gz \
    -p 1 -m 3 -e 4

# mark as approved
bash admin_benchmark_approval.sh

# submit trained model
medperf auth login -e modelowner@example.com
medperf mlcube submit -n trained \
    -m https://storage.googleapis.com/medperf-storage/testfl/mlcube_trained.yaml

# participatemedperf benchmark submit
medperf mlcube associate -b 1 -m 5 -y

# submit inference dataset
medperf auth login -e testcol@example.com
medperf dataset create -p 1 -d datasets/test -l datasets/test --name testdata --description testdata --location testdata
medperf dataset submit -d $(medperf dataset ls | grep test | tr -s " " | cut -d " " -f 1) -y

# associate dataset
medperf dataset associate -b 1 -d 3 -y

# approve associations
medperf auth login -e benchmarkowner@example.com
medperf association approve -b 1 -m 5
medperf association approve -b 1 -d 3

# run inference
medperf auth login -e testcol@example.com
medperf benchmark run -b 1 -d 3

# submit result
medperf result submit -r b1m5d3 -y
medperf result submit -r b1m3d3 -y


# read results
medperf auth login -e benchmarkowner@example.com
medperf result view -b 1

############ test other stuff
medperf auth login -e modelowner@example.com
medperf training ls
medperf aggregator ls
medperf training view 1
medperf aggregator view 1
medperf training list_associations