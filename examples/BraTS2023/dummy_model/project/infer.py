import os
import shutil


def run_inference(data_path, parameters, output_path):
    task = parameters["task"]
    if task == "segmentation":
        for k in os.listdir(data_path):
            file = os.path.join(data_path, k, f"{k}-t1c.nii.gz")
            shutil.copyfile(file, os.path.join(output_path, f"{k}.nii.gz"))

    elif task == "inpainting":
        for k in os.listdir(data_path):
            file = os.path.join(data_path, k, f"{k}-mask.nii.gz")
            shutil.copyfile(
                file, os.path.join(output_path, f"{k}-t1n-inference.nii.gz")
            )
    else:
        modalities = ["t1c", "t1n", "t2f", "t2w"]
        for k in os.listdir(data_path):
            found = []
            for file in os.listdir(os.path.join(data_path, k)):
                s1 = len("MMM.nii.gz")
                s2 = len(".nii.gz")
                found.append(file[-s1:-s2])

            missing = list(set(modalities).difference(found))[0]
            dummy = "t1c" if missing != "t1c" else "t2f"
            file = os.path.join(data_path, k, f"{k}-{dummy}.nii.gz")
            shutil.copyfile(file, os.path.join(output_path, f"{k}-{missing}.nii.gz"))
