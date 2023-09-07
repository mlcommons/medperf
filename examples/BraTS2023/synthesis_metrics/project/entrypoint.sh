#!/bin/bash

# Read arguments
while [ "${1:-}" != "" ]; do
    case "$1" in
        "--predictions"*)
            predictions="${1#*=}"
            ;;
        "--labels"*)
            labels="${1#*=}"
            ;;
        "--output_path"*)
            output_path="${1#*=}"
            ;;
        "--parameters_file"*)
            parameters_file="${1#*=}"
            ;;
        *)
            task=$1
            ;;
    esac
    shift
done

# validate arguments
if [ -z "$predictions" ]
then
    echo "--predictions is required"
    exit 1
fi

if [ -z "$labels" ]
then
    echo "--labels is required"
    exit 1
fi

if [ -z "$output_path" ]
then
    echo "--output_path is required"
    exit 1
fi

if [ -z "$parameters_file" ]
then
    echo "--parameters_file is required"
    exit 1
fi

if [ "$task" != "evaluate" ]
then
    echo "Invalid task: task should be evaluate"
    exit 1
fi

# Prepare input data to FeTS tool
/main_venv/bin/python /mlcube_project/prepare_data_input.py \
    --predictions $predictions \
    --labels $labels \
    --parameters_file $parameters_file \
    --intermediate_folder /data_renamed \
    --ssim_csv /ssim_data.csv

# Run FeTS tool
gpu_arg=$(/main_venv/bin/python /mlcube_project/parse_gpu_require.py --parameters_file $parameters_file)
FeTS_CLI_Segment -d /data_renamed -a fets_singlet,fets_triplet -lF STAPLE -g $gpu_arg -t 0

# Process FeTS tool output
/main_venv/bin/python /mlcube_project/process_tool_output.py \
    --intermediate_folder /data_renamed \
    --labels $labels \
    --parameters_file $parameters_file \
    --seg_csv /seg_data.csv \
    --fusion staple

# Run segmentation metrics
/seg_venv/bin/gandlf_generateBraTSMetrics -c BraTS-GLI -i /seg_data.csv -o /seg_metrics.yaml

# Run ssim metrics
/ssim_venv/bin/gandlf_generateMetrics -c /ssim_config.yaml -i /ssim_data.csv -o /ssim_metrics.yaml

# write final metrics file
/main_venv/bin/python /mlcube_project/write_metrics.py \
    --segmentation_metrics /seg_metrics.yaml \
    --ssim_metrics /ssim_metrics.yaml \
    --output_path $output_path
