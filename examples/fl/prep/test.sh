# mlcube run --mlcube ./mlcube --task prepare
# mlcube run --mlcube ./mlcube --task sanity_check
# mlcube run --mlcube ./mlcube --task statistics

medperf mlcube run --mlcube ./mlcube --task prepare -o ./logs_prep.log
medperf mlcube run --mlcube ./mlcube --task sanity_check -o ./logs_sanity.log
medperf mlcube run --mlcube ./mlcube --task statistics -o ./logs_stats.log
