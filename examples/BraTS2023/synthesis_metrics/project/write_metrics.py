import argparse
import os
import yaml


def main(segmentation_metrics, ssim_metrics, output_path):
    with open(segmentation_metrics) as f:
        segmentation_metrics = yaml.safe_load(f)

    with open(ssim_metrics) as f:
        ssim_metrics = yaml.safe_load(f)
    ssim_metrics = {key: val["ssim"] for key, val in ssim_metrics.items()}

    metrics = {"segmentation": segmentation_metrics, "ssim": ssim_metrics}
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(metrics, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--segmentation_metrics")
    parser.add_argument("--ssim_metrics")
    parser.add_argument("--output_path")

    args = parser.parse_args()
    main(args.segmentation_metrics, args.ssim_metrics, args.output_path)
