#!/bin/bash

# pretrained weights
export nnUNet_raw="/workspace/raw_data_base"
export nnUNet_preprocessed="/workspace/datasets"
export nnUNet_results="/workspace/weights"
export MKL_THREADING_LAYER=GNU

# Read arguments
while [ "${1:-}" != "" ]; do
    case "$1" in
        "--type"*)
            labels="${1#*=}"
            ;;
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
if [ -z "$type" ]
then
    echo "--type is required"
    exit 1
fi


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

mkdir /seg_output_folder

# Run glioma segmentation tool or metasis tool
if [ "$type" == "glioma" ]
then
    nnUNetv2_predict -d Dataset137_BraTS2021 -i "/data_renamed" -o "/seg_output_folder" -f  0 1 2 3 4 -tr nnUNetTrainer -c 3d_fullres -p nnUNetPlans
else
    nnUNetv2_predict -d Dataset133_BraTS_metasis_2024 -i "/data_renamed" -o "/seg_output_folder" -f  0 1 2 3 4 -tr nnUNetTrainer -c 3d_fullres -p nnUNetPlans
fi

# # Process nnunet tool output
/main_venv/bin/python /mlcube_project/process_tool_output.py \
    --intermediate_folder /seg_output_folder \
    --labels $labels \
    --parameters_file $parameters_file \
    --seg_csv /seg_data.csv \


# Run segmentation metrics
/seg_venv/bin/gandlf_generateBraTSMetrics -c BraTS-GLI -i /seg_data.csv -o /seg_metrics.yaml

# Run ssim metrics
/ssim_venv/bin/gandlf_generateMetrics -c /ssim_config.yaml -i /ssim_data.csv -o /ssim_metrics.yaml

# write final metrics file
/main_venv/bin/python /mlcube_project/write_metrics.py \
    --segmentation_metrics /seg_metrics.yaml \
    --ssim_metrics /ssim_metrics.yaml \
    --output_path $output_path