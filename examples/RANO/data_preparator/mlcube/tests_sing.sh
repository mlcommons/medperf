
DATA=./workspace/data

run() {
mlcube run --mlcube ./mlcube.yaml --task prepare --network=none --mount=ro --platform=singularity \
        report_file=report/report.yaml \
        labels_path=input_data \
        -Psingularity.run_args="-nce"
}

run_other() {
mlcube run --mlcube ./mlcube.yaml --task sanity_check --network=none --mount=ro --platform=singularity \
        -Psingularity.run_args="-nce"


mlcube run --mlcube ./mlcube.yaml --task statistics --network=none --mount=ro --platform=singularity \
        output_path=statistics/statistics.yaml \
        -Psingularity.run_args="-nce"

}

STARTTIME=$(date +%s.%N)


run

# manual review
cp $DATA/tumor_extracted/DataForQC/AAAC_1/2008.03.31/TumorMasksForQC/AAAC_1_2008.03.31_tumorMask_model_0.nii.gz \
   $DATA/tumor_extracted/DataForQC/AAAC_1/2008.03.31/TumorMasksForQC/finalized/AAAC_1_2008.03.31_tumorMask_model_0.nii.gz

cp $DATA/tumor_extracted/DataForQC/AAAC_1/2012.01.02/TumorMasksForQC/AAAC_1_2012.01.02_tumorMask_model_0.nii.gz \
   $DATA/tumor_extracted/DataForQC/AAAC_1/2012.01.02/TumorMasksForQC/finalized/AAAC_1_2012.01.02_tumorMask_model_0.nii.gz

cp $DATA/tumor_extracted/DataForQC/AAAC_2/2001.01.01/TumorMasksForQC/AAAC_2_2001.01.01_tumorMask_model_0.nii.gz \
   $DATA/tumor_extracted/DataForQC/AAAC_2/2001.01.01/TumorMasksForQC/finalized/AAAC_2_2001.01.01_tumorMask_model_0.nii.gz
# end manual review

run &
PID=$!

# prompt response
BREAK=0
while [ $BREAK -eq "0" ]
do
if [ -f $DATA/".prompt.txt" ];
    then BREAK=1;
else
    sleep 0.1s;
fi

done

echo -n "y" >> $DATA/.response.txt
# end prompt response

wait ${PID}

ENDTIME=$(date +%s.%N)
DIFF=$(echo "$ENDTIME - $STARTTIME" | bc)
echo $DIFF

run_other