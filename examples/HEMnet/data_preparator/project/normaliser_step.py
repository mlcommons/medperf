import argparse
from pathlib import Path
from mod_utils import (
    create_target_fitted_normaliser,
    dump_data,
)
from mod_constants import NORMALISER_PKL

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-n",
        "--normaliser",
        type=str,
        default="vahadane",
        choices=["none", "reinhard", "macenko", "vahadane"],
        help="H&E normalisation method",
    )
    parser.add_argument(
        "-std",
        "--standardise_luminosity",
        action="store_false",
        help="Disable luminosity standardisation",
    )
    parser.add_argument(
        "-a",
        "--align_mag",
        type=float,
        default=2,
        help="Magnification for aligning H&E and TP53 slide",
    )

    print("Running Normaliser step")
    args = parser.parse_args()

    ALIGNMENT_MAG = args.align_mag
    NORMALISER_METHOD = args.normaliser
    STANDARDISE_LUMINOSITY = args.standardise_luminosity

    normaliser = create_target_fitted_normaliser(ALIGNMENT_MAG, NORMALISER_METHOD, STANDARDISE_LUMINOSITY)
    dump_data(data_obj=normaliser, data_name=NORMALISER_PKL)
