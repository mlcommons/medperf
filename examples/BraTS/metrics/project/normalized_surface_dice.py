""" Adapted from https://github.com/mlcommons/GaNDLF/blob/master/GANDLF/metrics/segmentation.py"""

import SimpleITK as sitk

import torch
import numpy as np
import torch.nn.functional as F
from scipy.ndimage import _ni_support
from scipy.ndimage.morphology import (
    distance_transform_edt,
    binary_erosion,
    generate_binary_structure,
)
from .normalized_surface_dice import compute_surface_dice_from_images


def one_hot(segmask_tensor, class_list):
    """
    This function creates a one-hot-encoded mask from the segmentation mask Tensor and specified class list. Adapted from https://github.com/mlcommons/GaNDLF/blob/master/GANDLF/utils/tensor.py

    Args:
        segmask_tensor (torch.Tensor): The segmentation mask Tensor.
        class_list (list): The list of classes based on which one-hot encoding needs to happen.

    Returns:
        torch.Tensor: The one-hot encoded torch.Tensor
    """
    _segmask_tensor = segmask_tensor.unsqueeze(0).unsqueeze(0)
    batch_size = _segmask_tensor.shape[0]

    def_shape = _segmask_tensor.shape
    batch_stack = torch.zeros(
        def_shape[0],
        len(class_list),
        def_shape[2],
        def_shape[3],
        def_shape[4],
        dtype=torch.float32,
        device=_segmask_tensor.device,
    )

    for b in range(batch_size):
        # since the input tensor is 5D, with [batch_size, modality, x, y, z], we do not need to consider the modality dimension for labels
        segmask_array_iter = _segmask_tensor[b, 0, ...]
        bin_mask = segmask_array_iter == 0  # initialize bin_mask

        # this implementation allows users to combine logical operands
        class_idx = 0
        for _class in class_list:
            bin_mask = segmask_array_iter == int(_class)
            # we always ensure the append happens in dim 0
            batch_stack[b, class_idx, ...] = bin_mask.long().unsqueeze(0)
            class_idx += 1

    return batch_stack


def __surface_distances(result, reference, voxelspacing=None, connectivity=1):
    """
    The distances between the surface voxel of binary objects in result and their
    nearest partner surface voxel of a binary object in reference.

    Adopted from https://github.com/loli/medpy/blob/39131b94f0ab5328ab14a874229320efc2f74d98/medpy/metric/binary.py#L1195
    """
    result = np.atleast_1d(result.astype(bool))
    reference = np.atleast_1d(reference.astype(bool))
    if voxelspacing is not None:
        voxelspacing = _ni_support._normalize_sequence(voxelspacing, result.ndim)
        voxelspacing = np.asarray(voxelspacing, dtype=np.float64)
        if not voxelspacing.flags.contiguous:
            voxelspacing = voxelspacing.copy()

    # binary structure
    footprint = generate_binary_structure(result.ndim, connectivity)

    # test for emptiness
    if 0 == np.count_nonzero(result):
        # print(
        #     "The first supplied array does not contain any binary object.",
        #     file=sys.stderr,
        # )
        return 0
    if 0 == np.count_nonzero(reference):
        # print(
        #     "The second supplied array does not contain any binary object.",
        #     file=sys.stderr,
        # )
        return 0

    # extract only 1-pixel border line of objects
    result_border = result ^ binary_erosion(result, structure=footprint, iterations=1)
    reference_border = reference ^ binary_erosion(
        reference, structure=footprint, iterations=1
    )

    # compute average surface distance
    # Note: scipys distance transform is calculated only inside the borders of the
    #       foreground objects, therefore the input has to be reversed
    dt = distance_transform_edt(~reference_border, sampling=voxelspacing)
    sds = dt[result_border]

    return sds


def normalized_surface_dice(
    a: np.ndarray,
    b: np.ndarray,
    threshold: float,
    spacing: tuple = None,
    connectivity=1,
):
    """
    This implementation differs from the official surface dice implementation! These two are not comparable!!!!!
    The normalized surface dice is symmetric, so it should not matter whether a or b is the reference image
    This implementation natively supports 2D and 3D images. Whether other dimensions are supported depends on the
    __surface_distances implementation in medpy
    :param a: image 1, must have the same shape as b
    :param b: image 2, must have the same shape as a
    :param threshold: distances below this threshold will be counted as true positives. Threshold is in mm, not voxels!
    (if spacing = (1, 1(, 1)) then one voxel=1mm so the threshold is effectively in voxels)
    must be a tuple of len dimension(a)
    :param spacing: how many mm is one voxel in reality? Can be left at None, we then assume an isotropic spacing of 1mm
    :param connectivity: see scipy.ndimage.generate_binary_structure for more information. I suggest you leave that
    one alone
    :return:
    """
    assert all(
        [i == j for i, j in zip(a.shape, b.shape)]
    ), "a and b must have the same shape. a.shape= %s, " "b.shape= %s" % (
        str(a.shape),
        str(b.shape),
    )
    if spacing is None:
        spacing = tuple([1 for _ in range(len(a.shape))])
    a_to_b = __surface_distances(a, b, spacing, connectivity)
    b_to_a = __surface_distances(b, a, spacing, connectivity)

    if isinstance(a_to_b, int):
        return 0
    if isinstance(b_to_a, int):
        return 0
    numel_a = len(a_to_b)
    numel_b = len(b_to_a)
    tp_a = np.sum(a_to_b <= threshold) / numel_a
    tp_b = np.sum(b_to_a <= threshold) / numel_b
    fp = np.sum(a_to_b > threshold) / numel_a
    fn = np.sum(b_to_a > threshold) / numel_b
    dc = (tp_a + tp_b) / (
        tp_a + tp_b + fp + fn + 1e-8
    )  # 1e-8 just so that we don't get div by 0
    return dc


def compute_surface_dice_from_images(
    input_prediction,
    input_target,
    tolerance=1.0,
):
    """
    Compute the surface dice from images.

    Args:
        input_prediction (str): The prediction image file.
        input_target (str): The target image file.
        tolerance (float): Tolerance in terms of mm.
    """
    # Read the images
    prediction_img = sitk.ReadImage(input_prediction)
    target_img = sitk.ReadImage(input_target)

    assert (
        prediction_img.GetSize() == target_img.GetSize()
    ), "The prediction and target images must have the same size."
    assert (
        prediction_img.GetSpacing() == target_img.GetSpacing()
    ), "The prediction and target images must have the same spacing."
    prediction = torch.from_numpy(sitk.GetArrayFromImage(prediction_img)).long()
    target = torch.from_numpy(sitk.GetArrayFromImage(target_img)).long()

    class_list = [0, 1, 2, 4]
    predictions_hot = one_hot(prediction, class_list)
    target_hot = one_hot(target, class_list)

    ## convert prediction and target to ET, TC, WT
    ## calculate surface dice for each class
    ## return a dictionary of surface dice for each class

    predictions_tc = predictions_hot[:, 1, ...] + predictions_hot[:, 3, ...]
    predictions_et = predictions_hot[:, 3, ...]
    predictions_wt = predictions_hot[:, 1, ...] + predictions_hot[:, 2, ...] + predictions_hot[:, 3, ...]

    target_tc = target_hot[:, 1, ...] + target_hot[:, 3, ...]
    target_et = target_hot[:, 3, ...]
    target_wt = target_hot[:, 1, ...] + target_hot[:, 2, ...] + target_hot[:, 3, ...]

    sd = {}
    base_key_to_use = "NormalizedSurfaceDice_"

    sd[base_key_to_use + "TC"] = normalized_surface_dice(
        predictions_tc[0, ...].numpy(),
        target_tc[0, ...].numpy(),
        tolerance,
        spacing=prediction_img.GetSpacing(),
        connectivity=1,
    )

    sd[base_key_to_use + "ET"]  = normalized_surface_dice(
        predictions_et[0, ...].numpy(),
        target_et[0, ...].numpy(),
        tolerance,
        spacing=prediction_img.GetSpacing(),
        connectivity=1,
    )

    sd[base_key_to_use + "WT"]  = normalized_surface_dice(
        predictions_wt[0, ...].numpy(),
        target_wt[0, ...].numpy(),
        tolerance,
        spacing=prediction_img.GetSpacing(),
        connectivity=1,
    )

    print(f"Normalized Surface Dice: {sd}")
    return sd
