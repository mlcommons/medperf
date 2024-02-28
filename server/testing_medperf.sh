# TODO: remove me from the repo

# setup dev server or reset db
bash reset_db.sh
sudo rm -rf keys
sudo rm -rf /home/hasan/.medperf
# seed
python seed.py


medperf profile ls
medperf profile activate local
medperf profile ls

# move folder as a created dataset
cp -r /home/hasan/work/openfl_ws/9d56e799a9e63a6c3ced056ebd67eb6381483381 /home/hasan/.medperf/localhost_8000/data/

# login
medperf auth login -e testbo@example.com

# register mlcube
medperf mlcube submit -n testfl \
    -m https://storage.googleapis.com/medperf-storage/testfl/mlcube-cpu.yaml?v=1 \
    -p https://storage.googleapis.com/medperf-storage/testfl/parameters-cpu.yaml \
    -a https://storage.googleapis.com/medperf-storage/testfl/additional.tar.gz


# register training exp
medperf training submit -n testtrain -d testtrain -p 1 -m 5

# mark as approved
curl -sk -X PUT https://localhost:8000/api/v0/training/1/ -d '{"approval_status": "APPROVED"}' -H 'Content-Type: application/json' -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJjdXN0b21fY2xhaW1zL2VtYWlsIjoidGVzdGFkbWluQGV4YW1wbGUuY29tIiwiaXNzIjoiaHR0cHM6Ly9sb2NhbGhvc3Q6ODAwMC8iLCJzdWIiOiJ0ZXN0YWRtaW4iLCJhdWQiOiJodHRwczovL2xvY2FsaG9zdC1sb2NhbGRldi8iLCJpYXQiOjE2OTA1NTIxMjQsImV4cCI6MTE2OTA1NTIxMjR9.PbAxtzBxPfipnuYGPx90P2_K-2V7jPSdPEhzHEW6u4KnUQU8Gul6xrwLsGlgdD19A6EzUtgfQxW2Lk2OITcOD0nbXcjUgPyduLozMXDdTwom19429g7Q5eWOppWdMImirX3OygWaqx587Q_OL73HZuCjFcEWwyGnhB62oruVRcM6uDWz4xVmGcAwdtMzCBYvQj9_C-Hnt9IYPgnKesXPr_AP98-bdQx2EBahXtQW1HaARgabZp3SLaCDY9I6h91B7NQ-PDWpuDxd0UamHSaq9dNPbd0SsR6ajl80wOKQaZF3be_TKJW0e0l7L4tnsbbSW23fR1utSH2PlNFPBx3uGGe2Aqirdq16fAWqvDNO8-kiVRpeikp0ze17lTYqtw2-GZIxXyc8rG-NPxz7R5lMg7ARu99e5nLGFHpV5sMNUoXKx5zoPO7Y7cO5mdzm0C_2DARB7imagKsL5eLc5fcYDEZBl0FtkDgT_CY3FEuH_X3DgPwEP6wE2IFGnU1zEXtuNd1XSUxvxxZ0_afoX54qNuz3m9qzAKuYJkkziiApdIPE_bXX2ox3-Z_Q5RfqvtLRJoE64FaOMr_6xCq_77hpPDpWACQaXCwn736-Jl8nP1HcGvdDa980dzKaih4mQ-FtFZ8xhMXU7jA_Bur9e2tg51TxBzAyd4t4NNk-gYaSUPU"

# register aggregator
medperf auth login -e testmo@example.com
medperf aggregator submit -n testagg -a hasan-HP-ZBook-15-G3 -p 50273

# associate aggregator
medperf aggregator associate -a 1 -t 1


# register dataset
medperf auth login -e testdo@example.com
medperf dataset submit -d 9d56e799a9e63a6c3ced056ebd67eb6381483381

# associate dataset
medperf training associate_dataset -t 1 -d 1

# approve associations
medperf auth login -e testbo@example.com
medperf training approve_association -t 1 -a 1
medperf training approve_association -t 1 -d 1


# test nonimportant stuff
# medperf training ls
# medperf aggregator ls
# medperf training view 1
# medperf aggregator view 1
# medperf training list_associations

# lock experiment
medperf training lock -t 1

# # start aggregator
gnome-terminal -- bash -c "medperf aggregator start -a 1 -t 1; bash"

# # start collaborator
medperf training run -d 1 -t 1
