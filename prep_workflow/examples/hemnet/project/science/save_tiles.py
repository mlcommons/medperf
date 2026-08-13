import argparse
from mod_utils import load_numpy_array, load_slides_by_prefix, save_train_tiles, load_df, dump_df
from mod_constants import (
    OUTPUT_PATH,
    U_MASK_FILTERED,
    NON_C_MASK_FILTERED,
    C_MASK_FILTERED,
    T_MASK_FILTERED,
)
from slide import tile_gen_at_mag

from HEMnet_train_dataset import restricted_float
import time
import numpy as np
import os


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

    print("Saving tiles from Slide: {0}".format(PREFIX))

    start = time.perf_counter()
    he_slide, _ = load_slides_by_prefix(PREFIX)
    u_mask_filtered = load_numpy_array(U_MASK_FILTERED, PREFIX)
    c_mask_filtered = load_numpy_array(C_MASK_FILTERED, PREFIX)
    non_c_mask_filtered = (load_numpy_array(NON_C_MASK_FILTERED, PREFIX),)
    t_mask_filtered = load_numpy_array(T_MASK_FILTERED, PREFIX)
    performance_df = load_df(subdir=PREFIX)
    end = time.perf_counter()
    print(f"Time spent on reloading normaliser and slides: {end-start}s")

    ##############
    # Save Tiles #
    ##############

    # Make Directory to save tiles
    TILES_PATH = OUTPUT_PATH.joinpath("tiles_" + str(TILE_MAG) + "x")
    os.makedirs(TILES_PATH, exist_ok=True)

    # Save tiles
    tgen = tile_gen_at_mag(he_slide, TILE_MAG, OUTPUT_TILE_SIZE)
    save_train_tiles(
        TILES_PATH,
        tgen,
        c_mask_filtered,
        t_mask_filtered,
        u_mask_filtered,
        prefix=PREFIX,
    )

    non_cancer_tiles = np.invert(non_c_mask_filtered).sum()

    uncertain_tiles = np.invert(u_mask_filtered).sum()

    cancer_tiles = np.invert(c_mask_filtered).sum()

    performance_df["Cancer_Tiles"] = cancer_tiles
    performance_df["Uncertain_Tiles"] = uncertain_tiles
    performance_df["Non_Cancer_Tiles"] = non_cancer_tiles

    dump_df(performance_df, subdir=PREFIX)
