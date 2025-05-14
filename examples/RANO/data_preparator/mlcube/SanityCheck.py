import os, argparse, sys, platform
from copy import deepcopy
from datetime import date
import SimpleITK as sitk
import numpy as np


def read_image_with_min_check(filename):
    """
    this function fixes negatives by scaling
    if min(input) < 0:
      for all x in image:
        if x != 0:
          x -= min
    """
    input_image = sitk.ReadImage(filename)
    input_image_array = sitk.GetArrayFromImage(input_image)
    min = np.min(input_image_array)

    # fixme: apply following logic
    # check for connected components with less than 100 voxels
    ## if less than the threshold, then apply above logic to the negative voxels
    ## else, give error to user for manual QC
    if min < 0:
        print("Negative values in", filename)

    return input_image


def imageSanityCheck(targetImageFile, inputImageFile) -> bool:
    """
    This function does sanity checking of 2 images
    """
    targetImage = read_image_with_min_check(targetImageFile)
    inputImage = read_image_with_min_check(inputImageFile)

    size = targetImage.GetSize()
    size_expected = np.array([240, 240, 155])
    if not (np.array_equal(size, size_expected)):
        print(
            "Size for target image, '"
            + targetImageFile
            + "' is not in the BraTS format",
            size_expected,
            file=sys.stderr,
        )
        return False

    if targetImage.GetDimension() != 3:
        print(
            "Dimension for target image, '" + targetImageFile + "' is not 3",
            file=sys.stderr,
        )
        return False

    if inputImage.GetDimension() != 3:
        print(
            "Dimension for input image, '" + inputImageFile + "' is not 3",
            file=sys.stderr,
        )
        return False

    commonMessage = (
        " mismatch for target image, '"
        + targetImageFile
        + "' and input image, '"
        + inputImageFile
        + "'"
    )
    problemsIn = ""
    returnTrue = True

    if targetImage.GetSize() != inputImage.GetSize():
        if not problemsIn:
            problemsIn += "Size"
        else:
            problemsIn += ", Size"
        returnTrue = False

    if targetImage.GetOrigin() != inputImage.GetOrigin():
        if not problemsIn:
            problemsIn += "Origin"
        else:
            problemsIn += ", Origin"
        returnTrue = False

    if targetImage.GetSpacing() != inputImage.GetSpacing():
        if not problemsIn:
            problemsIn += "Spacing"
        else:
            problemsIn += ", Spacing"
        returnTrue = False

    if returnTrue:
        return True
    else:
        print(problemsIn + commonMessage, file=sys.stderr)
        return False


def checkBraTSLabels(
    subject_id, currentLabelFile, label_values_expected=np.array([0, 1, 2, 4])
) -> str:
    """
    This function checks for the expected labels and returns a string that will be provided as output for user
    """
    returnString = ""
    mask_array = sitk.GetArrayFromImage(sitk.ReadImage(currentLabelFile))
    # get unique elements and their counts
    unique, counts = np.unique(mask_array, return_counts=True)
    # this is for the case where the label contains numbers other than 0,1,2,4
    if not (np.array_equal(unique, label_values_expected)):
        for j in range(0, len(unique)):  # iterate over a range to get counts easier
            if not (unique[j] in label_values_expected):
                if (
                    counts[j] > 1000
                ):  # threshold for mis-labelling, anything less is ignored
                    returnString += (
                        subject_id
                        + ","
                        + currentLabelFile
                        + ","
                        + str(unique[j])
                        + ","
                        + str(counts[j])
                        + "\n"
                    )

    return returnString


def fixForLabelThree(currentLabelFile):
    """
    This function checks for the label '3' and changes it to '4' and save it in the same location
    """
    base_image = sitk.ReadImage(currentLabelFile)
    mask_array = sitk.GetArrayFromImage(sitk.ReadImage(currentLabelFile))
    unique = np.sort(np.unique(mask_array))
    if unique[-1] == 3:
        mask_array[mask_array == 3] = 4
        image_to_write = sitk.GetImageFromArray(mask_array)
        image_to_write.CopyInformation(base_image)
        sitk.WriteImage(image_to_write, currentLabelFile)


def main():
    copyrightMessage = (
        "Contact: admin@fets.ai\n\n"
        + "This program is NOT FDA/CE approved and NOT intended for clinical use.\nCopyright (c) "
        + str(date.today().year)
        + " University of Pennsylvania. All rights reserved."
    )
    parser = argparse.ArgumentParser(
        prog="SanityCheck",
        formatter_class=argparse.RawTextHelpFormatter,
        description="This application performs rudimentary sanity checks the input data folder for FeTS training.\n\n"
        + copyrightMessage,
    )
    parser.add_argument(
        "-inputDir",
        type=str,
        help="The input directory (DataForFeTS) that needs to be checked",
        required=True,
    )
    parser.add_argument(
        "-outputFile",
        type=str,
        help="The CSV file of outputs, which is only generated if there are problematic cases",
        required=True,
    )

    args = parser.parse_args()
    inputDir = args.inputDir

    if not os.path.isdir(inputDir):
        sys.exit("The specified inputDir is not present, please try again")

    errorMessage = "Subject_ID,Recommendation_for_initial_annotations\n"
    numberOfProblematicCases = 0

    # initialize modality dict
    files_to_check = {
        "T1": "_t1.nii.gz",
        "T1CE": "_t1ce.nii.gz",
        "T2": "_t2.nii.gz",
        "FL": "_flair.nii.gz",
        "MASK": "_final_seg.nii.gz",
    }

    label_values_expected = np.array([0, 1, 2, 4])  # initialize label array

    for dirs in os.listdir(inputDir):
        if (dirs != "logs") and (
            dirs != "split_info"
        ):  # don't perform sanity check for the 'logs' folder
            currentSubjectDir = os.path.join(inputDir, dirs)
            if os.path.isdir(currentSubjectDir):  # for detected subject dir
                filesInDir = os.listdir(
                    currentSubjectDir
                )  # get all files in each directory
                files_for_subject = {}
                for i in range(len(filesInDir)):
                    for modality in files_to_check:  # check all modalities
                        if filesInDir[i].endswith(
                            files_to_check[modality]
                        ):  # if modality detected, populate subject dict
                            files_for_subject[modality] = os.path.abspath(
                                os.path.join(currentSubjectDir, filesInDir[i])
                            )

                currentSubjectsLabelIsAbsent = (
                    False  # check if current subject's final_seg is present or not
                )
                all_modalities_present = True
                if (
                    len(files_for_subject) != 5
                ):  # if all modalities are not present, add exit statement
                    if (
                        (len(files_for_subject) == 4) and ("MASK" in files_for_subject)
                    ) or (len(files_for_subject) < 4):
                        numberOfProblematicCases += 1
                        errorMessage += (
                            dirs + ",All_required_modalities_are_not_present.\n"
                        )
                        all_modalities_present = False

                if all_modalities_present and len(files_for_subject) > 0:
                    first, *rest = files_for_subject.items()  # split the dict
                    for i in range(0, len(rest)):
                        if not (
                            imageSanityCheck(first[1], rest[i][1])
                        ):  # image sanity check
                            numberOfProblematicCases += 1
                            errorMessage += (
                                dirs
                                + ",Image_dimension/size/origin/spacing_mismatch_between_"
                                + first[0]
                                + "_and_"
                                + rest[i][0]
                                + "\n"
                            )

                    currentSubjectsLabelIsProblematic = (
                        False  # check if current subject's label has issues
                    )
                    if "MASK" in files_for_subject:
                        currentLabelFile = files_for_subject["MASK"]
                        fixForLabelThree(currentLabelFile)
                        returnString = checkBraTSLabels(dirs, currentLabelFile)
                        if (
                            returnString
                        ):  # if there is something present in the return string
                            numberOfProblematicCases += 1
                            currentSubjectsLabelIsProblematic = True
                            errorMessage += returnString
                    else:
                        currentSubjectsLabelIsAbsent = True

                    fusionToRecommend = ""
                    segmentationsForQCPresent = True
                    problematicSegmentationMessage = ""
                    if (
                        currentSubjectsLabelIsProblematic
                        or currentSubjectsLabelIsAbsent
                    ):  # if final_seg is absent or is problematic
                        segmentationsFolder = os.path.join(
                            currentSubjectDir, "SegmentationsForQC"
                        )
                        if os.path.isdir(segmentationsFolder):
                            segmentationFiles = os.listdir(
                                segmentationsFolder
                            )  # get all files in each directory
                            for i in range(len(segmentationFiles)):
                                if (
                                    "fused" in segmentationFiles[i]
                                ):  # only perform checks for fusion results
                                    currentLabelFile = os.path.join(
                                        segmentationsFolder, segmentationFiles[i]
                                    )
                                    returnString = checkBraTSLabels(
                                        dirs, currentLabelFile
                                    )
                                    if (
                                        returnString
                                    ):  # if there is something present in the return string
                                        problematicSegmentationMessage += returnString
                                    else:
                                        if not (
                                            "staple" in fusionToRecommend
                                        ):  # overwrite the fusion result to recommend if not staple that was fine
                                            fusionToRecommend = currentLabelFile

                            if not fusionToRecommend:
                                errorMessage += problematicSegmentationMessage
                            if not (
                                "staple" in fusionToRecommend
                            ):  # recommend nnunet or deepscan if not staple
                                if not ("itkvoting" in fusionToRecommend):
                                    if not ("majorityvoting" in fusionToRecommend):
                                        fusionToRecommend = "nnunet_or_deepscan"
                                    else:
                                        fusionToRecommend = "majorityvoting"
                                else:
                                    fusionToRecommend = "itkvoting"
                            else:
                                fusionToRecommend = "staple"

                        else:
                            errorMessage += (
                                dirs + ",SegmentationsForQC_folder_is_absent\n"
                            )
                            numberOfProblematicCases += 1
                            segmentationsForQCPresent = False
                        # errorMessage += dirs + ',Label_file_absent,N.A.,N.A.\n'

                    if currentSubjectsLabelIsAbsent and segmentationsForQCPresent:
                        numberOfProblematicCases += 1
                        if fusionToRecommend:
                            errorMessage += dirs + "," + fusionToRecommend + "\n"
                        else:
                            errorMessage += (
                                dirs
                                + ",final_seg_absent_and_use_either_nnunet_or_deepscan,N.A.,N.A.\n"
                            )

    if numberOfProblematicCases > 0:
        # print(errorMessage)
        with open(args.outputFile, "a") as the_file:
            the_file.write(errorMessage)
        sys.exit(
            "There were subjects with either missing annotations or where annotations had problematic labels. Please see the recommendation(s) for new initialization in the outputFile: '"
            + args.outputFile
            + "'"
        )
    else:
        print("Congratulations, all subjects are fine and ready to train!")


if __name__ == "__main__":
    if platform.system().lower() == "darwin":
        sys.exit("macOS is not supported")
    else:
        main()
