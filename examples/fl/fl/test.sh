gnome-terminal -- bash -c "medperf mlcube run --mlcube ./mlcube_agg --task start_aggregator -P 50273; bash"
gnome-terminal -- bash -c "medperf mlcube run --mlcube ./mlcube_col1 --task train -e COLLABORATOR_CN=abc; bash"
gnome-terminal -- bash -c "medperf mlcube run --mlcube ./mlcube_col2 --task train -e COLLABORATOR_CN=defg; bash"
gnome-terminal -- bash -c "medperf mlcube run --mlcube ./mlcube_col3 --task train -e COLLABORATOR_CN=hij; bash"
