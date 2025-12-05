import argparse
from mod_utils import save_img, dump_numpy_array, load_pil_image
from mod_constants import (
    OUTPUT_PATH,
    HE_FILTERED_NPY,
    TP53_FILTERED_NPY,
    U_MASK_FILTERED,
    C_MASK_FILTERED,
    NON_C_MASK_FILTERED,
    T_MASK_FILTERED,
)
from utils import (
    cancer_mask,
    tissue_mask_grabcut,
    plot_masks,
)

from HEMnet_train_dataset import uncertain_mask, restricted_float
import time
import numpy as np


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--subject-subdir",
        type=str,
        required=True,
        help="Prefix that defines the slides used in this step.",
    )
    parser.add_argument(
        "-a",
        "--align_mag",
        type=float,
        default=2,
        help="Magnification for aligning H&E and TP53 slide",
    )
    parser.add_argument(
        "-m",
        "--tile_mag",
        type=float,
        default=10,
        help="Magnification for generating tiles",
    )
    parser.add_argument(
        "-ts", "--tile_size", type=int, default=224, help="Output tile size in pixels"
    )
    parser.add_argument(
        "-c",
        "--cancer_thresh",
        type=restricted_float,
        default=0.39,
        help="TP53 threshold for cancer classification",
    )
    parser.add_argument(
        "-nc",
        "--non_cancer_thresh",
        type=restricted_float,
        default=0.40,
        help="TP53 threshold for non-cancer classification",
    )
    parser.add_argument(
        "-v", "--verbosity", action="store_true", help="Increase output verbosity"
    )

    args = parser.parse_args()
    # PATHS
    PREFIX = args.subject_subdir

    # User selectable parameters
    ALIGNMENT_MAG = args.align_mag
    VERBOSE = args.verbosity
    CANCER_THRESH = args.cancer_thresh
    NON_CANCER_THRESH = args.non_cancer_thresh
    TILE_MAG = args.tile_mag
    OUTPUT_TILE_SIZE = args.tile_size

    print("Running Mask Generation step on Slide: {0}".format(PREFIX))

    start = time.perf_counter()
    he_filtered = load_pil_image(HE_FILTERED_NPY, PREFIX)
    tp53_filtered = load_pil_image(TP53_FILTERED_NPY, PREFIX)
    end = time.perf_counter()
    print(f"Time spent on reloading filtered images: {end-start}s")
    ####################################
    # Generate cancer and tissue masks #
    ####################################

    # Scale tile size for alignment mag
    tile_size = OUTPUT_TILE_SIZE * ALIGNMENT_MAG / TILE_MAG

    # Generate cancer mask and tissue mask from filtered tp53 image
    c_mask = cancer_mask(tp53_filtered, tile_size, 250).astype(np.bool)
    t_mask_tp53 = tissue_mask_grabcut(tp53_filtered, tile_size)
    t_mask_he = tissue_mask_grabcut(he_filtered, tile_size)

    # Generate tissue mask with tissue common to both the TP53 and H&E image
    t_mask = np.logical_not(np.logical_not(t_mask_tp53) & np.logical_not(t_mask_he))

    # Generate uncertain mask
    u_mask = uncertain_mask(tp53_filtered, tile_size, CANCER_THRESH, NON_CANCER_THRESH)
    u_mask_filtered = np.logical_not(np.logical_not(u_mask) & np.logical_not(t_mask))

    # Filter tissue mask such that any uncertain tiles are removed
    t_mask_filtered = np.zeros(t_mask.shape)
    for x in range(t_mask.shape[0]):
        for y in range(t_mask.shape[1]):
            if t_mask[x, y] == 0 and u_mask[x, y] == 1:
                t_mask_filtered[x, y] = False
            else:
                t_mask_filtered[x, y] = True

    non_c_mask = np.invert(c_mask)
    non_c_mask = np.logical_not(
        np.logical_and(np.logical_not(non_c_mask), np.logical_not(t_mask_filtered))
    )

    # If Slide is normal
    if "_N_" in PREFIX:
        # if True:
        # Merge cancer mask with uncertain mask
        # This marks all tiles that are uncertain or cancer as uncertain
        u_mask_filtered = np.logical_not(
            np.logical_or(np.logical_not(u_mask_filtered), np.logical_not(c_mask))
        )
        # Blank out cancer mask so no cancer tiles exist
        c_mask_filtered = np.ones(c_mask.shape, dtype=bool)
        # Non cancer tiles are tiles that are in the tissue and not cancer
        non_c_mask_filtered = np.logical_not(
            np.logical_and(np.logical_not(non_c_mask), np.logical_not(t_mask_filtered))
        )
        if VERBOSE:
            print("Normal Slide Identified")

    # If Slide is cancerous
    if "T" in PREFIX:
        # if False:
        # Merge non-cancer mask with uncertain mask
        u_mask_filtered = np.logical_not(
            np.logical_or(np.logical_not(non_c_mask), np.logical_not(u_mask_filtered))
        )
        # Blank out non cancer mask
        non_c_mask_filtered = np.ones(non_c_mask.shape, dtype=bool)
        # Cancer tile are tiles that are in the tissue and not cancer
        # Make sure all cancer tiles exist in the tissue mask
        c_mask_filtered = np.logical_not(
            np.logical_not(c_mask) & np.logical_not(t_mask_filtered)
        )

        # Overlay masks onto TP53 and H&E Image
        if VERBOSE:
            print("Cancer Slide Identified")
            overlay_tp53 = plot_masks(
                tp53_filtered,
                c_mask_filtered,
                t_mask_filtered,
                tile_size,
                u_mask_filtered,
            )
            save_img(
                overlay_tp53.convert("RGB"),
                OUTPUT_PATH.joinpath(PREFIX + "TP53_overlay.jpeg"),
                "JPEG",
            )

            overlay_he = plot_masks(
                he_filtered,
                c_mask_filtered,
                t_mask_filtered,
                tile_size,
                u_mask_filtered,
            )
            save_img(
                overlay_he.convert("RGB"),
                OUTPUT_PATH.joinpath(PREFIX + "HE_overlay.jpeg"),
                "JPEG",
            )

    arrays_to_save_tuples = [
        (u_mask_filtered, U_MASK_FILTERED),
        (c_mask_filtered, C_MASK_FILTERED),
        (non_c_mask_filtered, NON_C_MASK_FILTERED),
        (t_mask_filtered, T_MASK_FILTERED),
    ]

    for array_to_save_tuple in arrays_to_save_tuples:
        array, filename = array_to_save_tuple
        dump_numpy_array(array, filename, PREFIX)
