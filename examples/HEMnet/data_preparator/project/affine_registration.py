import argparse
from mod_utils import (
    load_pil_image,
    save_fig,
    dump_sitk_transform,
    dump_sitk_image,
    get_fixed_and_moving_images,
    load_df,
    dump_df,
)
import matplotlib.pyplot as plt
import SimpleITK as sitk
from mod_constants import (
    OUTPUT_PATH,
    INTERPOLATOR,
    AFFINE_TRANSFORM_HDF,
    MOVING_RESAMPLED_AFFINE_NPY,
    TP53_GRAY,
    HE_GRAY,
)
from utils import (
    calculate_mutual_info,
    get_pil_from_itk,
    start_plot,
    update_multires_iterations,
    update_plot,
    plot_metric,
    end_plot,
)
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
        "-v", "--verbosity", action="store_true", help="Increase output verbosity"
    )

    args = parser.parse_args()
    # PATHS
    PREFIX = args.subject_subdir

    # User selectable parameters
    ALIGNMENT_MAG = args.align_mag
    VERBOSE = args.verbosity

    print("Runing Affine Registration step on slide: {0}".format(PREFIX))

    start = time.perf_counter()
    tp53_gray = load_pil_image(TP53_GRAY, PREFIX)
    he_gray = load_pil_image(HE_GRAY, PREFIX)
    fixed_img, moving_img = get_fixed_and_moving_images(tp53_gray, he_gray)
    performance_df = load_df(subdir=PREFIX)
    end = time.perf_counter()

    print(f"Time spent on reloading normaliser and slides: {end-start}s")

    initial_transform = sitk.CenteredTransformInitializer(
        fixed_img,
        moving_img,
        sitk.Euler2DTransform(),
        sitk.CenteredTransformInitializerFilter.GEOMETRY,
    )
    affine_method = sitk.ImageRegistrationMethod()

    # Similarity metric settings.
    affine_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    affine_method.SetMetricSamplingStrategy(affine_method.RANDOM)
    affine_method.SetMetricSamplingPercentage(0.15)

    affine_method.SetInterpolator(INTERPOLATOR)

    # Optimizer settings.
    affine_method.SetOptimizerAsGradientDescent(
        learningRate=1,
        numberOfIterations=100,
        convergenceMinimumValue=1e-6,
        convergenceWindowSize=20,
    )
    affine_method.SetOptimizerScalesFromPhysicalShift()

    # Setup for the multi-resolution framework.
    affine_method.SetShrinkFactorsPerLevel(shrinkFactors=[8, 4])
    affine_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[4, 2])
    affine_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

    # Don't optimize in-place, we would possibly like to run this cell multiple times.
    affine_method.SetInitialTransform(initial_transform, inPlace=False)

    # Connect all of the observers so that we can perform plotting during registration.
    affine_method.AddCommand(sitk.sitkStartEvent, start_plot)
    affine_method.AddCommand(
        sitk.sitkMultiResolutionIterationEvent, update_multires_iterations
    )
    affine_method.AddCommand(
        sitk.sitkIterationEvent, lambda: update_plot(affine_method)
    )

    affine_transform = affine_method.Execute(
        sitk.Cast(fixed_img, sitk.sitkFloat32),
        sitk.Cast(moving_img, sitk.sitkFloat32),
    )

    if VERBOSE:
        affine_fig = plot_metric(
            "Plot of mutual information cost in affine registration"
        )
        plt.show()
        save_fig(affine_fig, OUTPUT_PATH.joinpath(PREFIX + "affine_metric_plot.jpeg"))
        end_plot()

        print(
            "Affine Optimizer's stopping condition, {0}".format(
                affine_method.GetOptimizerStopConditionDescription()
            )
        )

    # Compute the mutual information between the two images after affine registration
    moving_resampled_affine = sitk.Resample(
        moving_img,
        fixed_img,
        affine_transform,
        INTERPOLATOR,
        0.0,
        moving_img.GetPixelID(),
    )
    affine_mutual_info = calculate_mutual_info(
        np.array(he_gray), np.array(get_pil_from_itk(moving_resampled_affine))
    )
    if VERBOSE:
        print("Affine mutual information metric: {0}".format(affine_mutual_info))

    performance_df["Affine_Mutual_Info"] = affine_mutual_info

    dump_df(performance_df, subdir=PREFIX)

    dump_sitk_image(
        sitk_image=moving_resampled_affine,
        data_name=MOVING_RESAMPLED_AFFINE_NPY,
        subdir=PREFIX,
    )
    dump_sitk_transform(
        sitk_transform=affine_transform, data_name=AFFINE_TRANSFORM_HDF, subdir=PREFIX
    )
