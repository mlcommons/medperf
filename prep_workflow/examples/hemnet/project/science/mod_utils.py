import os
from openslide import open_slide
from mod_constants import INPUT_PATH, TEMP_DATA_PATH, NORMALISER_PKL, PERFORMANCE_DF
from slide import read_slide_at_mag
from normaliser import IterativeNormaliser
import pickle
import SimpleITK as sitk
import numpy as np
from utils import get_pil_from_itk
from PIL import Image
from utils import get_itk_from_pil
import pandas as pd


def save_img(img, path, img_type):
    img.save(path, img_type)


def save_fig(fig, path, dpi=300):
    fig.savefig(path, dpi=dpi)


def get_template_slide_from_dir(template_slide_path: str = None):
    input_dir = str(INPUT_PATH)
    template_dir = os.path.join(input_dir, "template")
    try:
        slides = [file for file in os.listdir(template_dir) if file.endswith(".svs")]

        template_slide_path = os.path.join(template_dir, slides[0])

        if len(slides) > 1:
            print(
                f"More than 1 slide found at {template_dir}. Using {template_slide_path} as the template."
            )
    except OSError:
        raise ValueError(
            f"Please provide an explicit template slide either with the -t option or by setting a single .svs file at the {os.path.join(template_dir)} directory!"
        )
    return template_slide_path


def create_target_fitted_normaliser(
    alignment_mag, normaliser_method, standardise_luminosity
) -> IterativeNormaliser:
    template_slide_path = get_template_slide_from_dir()

    print(
        f"Using slide located at {template_slide_path} as the template to instantiate normaliser."
    )
    template_slide = open_slide(str(template_slide_path))
    template_img = read_slide_at_mag(template_slide, alignment_mag).convert("RGB")

    normaliser = IterativeNormaliser(normaliser_method, standardise_luminosity)
    normaliser.fit_target(template_img)

    return normaliser


def _get_saved_file_full_path(filename, subdir: str = None):
    os.makedirs(TEMP_DATA_PATH, exist_ok=True)
    data_dir = TEMP_DATA_PATH
    if subdir is not None:
        data_dir = TEMP_DATA_PATH.joinpath(subdir)
        os.makedirs(data_dir, exist_ok=True)
    full_pickle_path = data_dir.joinpath(filename)
    return full_pickle_path


def dump_numpy_array(np_array, data_name: str, subdir: str = None):
    np_path = _get_saved_file_full_path(data_name, subdir)
    with open(np_path, "wb") as f:
        np.save(f, np_array)


def load_numpy_array(data_name: str, subdir: str = None):
    np_path = _get_saved_file_full_path(data_name, subdir)
    with open(np_path, "rb") as f:
        np_array = np.load(f)
    return np_array


def dump_pil_image(pil_image, data_name: str, subdir: str = None):
    as_np = np.array(pil_image)
    dump_numpy_array(as_np, data_name, subdir)


def load_pil_image(data_name: str, subdir: str = None):
    as_np = load_numpy_array(data_name, subdir)
    pil_image = Image.fromarray(as_np)
    return pil_image


def dump_sitk_image(sitk_image, data_name: str, subdir: str = None):
    as_pil = get_pil_from_itk(sitk_image)
    dump_pil_image(as_pil, data_name, subdir)


def load_sitk_image(data_name, subdir: str = None):
    as_np = load_numpy_array(data_name, subdir)
    as_itk = sitk.GetImageFromArray(as_np)
    return as_itk


def dump_sitk_transform(
    sitk_transform: sitk.Transform, data_name: str, subdir: str = None
):
    print(f"Dumping SITK transform {data_name}...")
    transform_path = str(_get_saved_file_full_path(data_name, subdir))
    sitk_transform.FlattenTransform()
    sitk_transform.WriteTransform(transform_path)


def load_sitk_transform(data_name, subdir: str = None):
    transform_path = str(_get_saved_file_full_path(data_name, subdir))
    sitk_transform = sitk.ReadTransform(transform_path)
    return sitk_transform


def dump_data(data_obj, data_name: str, subdir: str = None):
    full_path = _get_saved_file_full_path(data_name, subdir)
    with open(full_path, "wb") as f:
        pickle.dump(data_obj, f)
    print(f"Successfully dumped object {data_name} at {full_path}.")


def load_data(data_name: str, subdir: str = None):
    full_path = _get_saved_file_full_path(data_name, subdir)
    with open(full_path, "rb") as f:
        normalizer_obj = pickle.load(f)
    print(f"Successfully loaded object {data_name} from {full_path}.")
    return normalizer_obj


def dump_df(df: pd.DataFrame, df_name: str = PERFORMANCE_DF, subdir: str = None):
    full_path = _get_saved_file_full_path(df_name, subdir)
    df.to_csv(full_path, encoding="utf-8")


def load_df(df_name: str = PERFORMANCE_DF, subdir: str = None):
    full_path = _get_saved_file_full_path(df_name, subdir)
    df = pd.read_csv(full_path, encoding="utf-8", index_col=0)
    return df


def get_slide_names_by_prefix(prefix: str):
    relevant_filenames = sorted(
        [file for file in os.listdir(INPUT_PATH) if prefix in file],
        key=lambda file: (
            file.split("_")[0],
            file.split("_")[-1],
        ),  # Order by prefix (integer) then by suffix (HandE first, then TP53)
    )
    he_name, tp53_name = relevant_filenames
    return he_name, tp53_name


def load_slides_by_prefix(prefix: str):
    print(f"Loading slides with prefix {prefix}")
    relevant_filenames = get_slide_names_by_prefix(prefix)
    relevant_filepaths = sorted(
        [os.path.join(INPUT_PATH, file) for file in relevant_filenames]
    )

    he_path, tp53_path = relevant_filepaths

    tp53_slide = open_slide(tp53_path)
    he_slide = open_slide(he_path)

    print(f"Successfully loaded slides with prefix {prefix}.")
    return he_slide, tp53_slide


def load_and_magnify_slides_by_prefix(prefix: str, aligment_mag: float):
    he_slide, tp53_slide = load_slides_by_prefix(prefix)

    # Load Slides
    he = read_slide_at_mag(he_slide, aligment_mag)
    tp53 = read_slide_at_mag(tp53_slide, aligment_mag)
    print(f"Successfully loaded and magnified slides with prefix {prefix}.")
    return he, tp53


def get_fixed_and_moving_images(tp53_gray, he_gray):
    # Convert to ITK format
    tp53_itk = get_itk_from_pil(tp53_gray)
    he_itk = get_itk_from_pil(he_gray)

    fixed_img = he_itk
    moving_img = tp53_itk

    return fixed_img, moving_img


def save_train_tiles(
    path,
    tile_gen,
    cancer_mask,
    tissue_mask,
    uncertain_mask,
    prefix="",
    verbose: bool = False,
):
    """Save tiles for train dataset

    Parameters
    ----------
    path : Pathlib Path
    tile_gen : tile_gen
    cancer_mask : ndarray
    tissue_mask : ndarray
    uncertain_mask : ndarray
    prefix : str (optional)

    Returns
    -------
    None
    """
    normaliser = load_data(data_name=NORMALISER_PKL, subdir=prefix)
    os.makedirs(path.joinpath("cancer"), exist_ok=True)
    os.makedirs(path.joinpath("non-cancer"), exist_ok=True)
    os.makedirs(path.joinpath("uncertain"), exist_ok=True)
    x_tiles, y_tiles = next(tile_gen)

    if verbose:
        print("Whole Image Size is {0} x {1}".format(x_tiles, y_tiles))
    i = 0
    cancer = 0
    uncertain = 0
    non_cancer = 0
    for tile in tile_gen:
        img = tile.convert("RGB")
        ###
        img_norm = normaliser.transform_tile(img)
        ###
        # Name tile as horizontal position _ vertical position starting at (0,0)
        tile_name = prefix + str(np.floor_divide(i, x_tiles)) + "_" + str(i % x_tiles)
        if uncertain_mask.ravel()[i] == 0:
            img_norm.save(path.joinpath("uncertain", tile_name + ".jpeg"), "JPEG")
            uncertain += 1
        elif cancer_mask.ravel()[i] == 0:
            img_norm.save(path.joinpath("cancer", tile_name + ".jpeg"), "JPEG")
            cancer += 1
        elif tissue_mask.ravel()[i] == 0:
            img_norm.save(path.joinpath("non-cancer", tile_name + ".jpeg"), "JPEG")
            non_cancer += 1
        i += 1
    if verbose:
        print(
            "Cancer tiles: {0}, Non Cancer tiles: {1}, Uncertain tiles: {2}".format(
                cancer, non_cancer, uncertain
            )
        )
        print("Exported tiles for {0}".format(prefix))
