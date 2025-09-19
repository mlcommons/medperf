medperf auth logout
medperf auth login -e testdo2@example.com

medperf dataset submit --data_prep 2 \
  --data_path medperf_tutorial/col2 \
  --labels_path medperf_tutorial/col2 \
  --name col1data \
  --description "some data" \
  --location mymachine -y

medperf dataset prepare --data_uid 2

medperf dataset set_operational --data_uid 2 -y

medperf dataset associate  --data_uid 2 --training_exp_uid 1 -y

medperf dataset train --data_uid 2 --training_exp_id 1 -y
