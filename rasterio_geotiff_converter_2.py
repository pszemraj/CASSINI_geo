"""


https://rasterio.readthedocs.io/en/latest/installation.html


"""

import os
import pprint as pp
import shutil
import time
from datetime import datetime
from os import listdir
from os.path import join, isfile

import matplotlib.pyplot as plt
import rasterio
import wordninja
from cleantext import clean
from natsort import natsorted
from rasterio.dtypes import uint8
from rasterio.enums import Resampling
from rasterio.plot import show
from tqdm import tqdm

tif_dir_path = str(input("Enter path to folder with geotiff files -->"))
# -----------------------------------------------------------------
output_folder_name = "rasterio_conv_v2"
if not os.path.isdir(join(tif_dir_path, output_folder_name)):
    os.mkdir(join(tif_dir_path, output_folder_name))
    # make a place to store outputs if one does not exist
output_path_full = os.path.join(tif_dir_path, output_folder_name)
print("outputs will be in: \n", output_path_full)

# ----------------------------------------------------------------------------
import numpy as np


def rasterio_conv(input_path, output_path, verbose=False):
    # Read raster bands directly to Numpy arrays.
    #
    with rasterio.open(input_path) as src:
        placeholder_list = src.read()
        r, g, b, rest = placeholder_list[0], placeholder_list[1], placeholder_list[2], placeholder_list[3:]

    if verbose:
        print("there are {} additional bands".format(len(rest)))

    # Combine arrays in place. Expecting that the sum will
    # temporarily exceed the 8-bit integer range, initialize it as
    # a 64-bit float (the numpy default) array. Adding other
    # arrays to it in-place converts those arrays "up" and
    # preserves the type of the total array.
    total = np.zeros(r.shape)
    for band in r, g, b:
        total += band
    total /= 3

    # Write the product as a raster band to a new 8-bit file. For
    # the new file's profile, we start with the meta attributes of
    # the source file, but then change the band count to 1, set the
    # dtype to uint8, and specify LZW compression.
    profile = src.profile
    profile.update(dtype=rasterio.uint8, count=1, compress='lzw')

    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(total.astype(rasterio.uint8), 1)


def cleantxt_wrap(ugly_text):
    # a wrapper for clean text with options different than default

    # https://pypi.org/project/clean-text/
    cleaned_text = clean(ugly_text,
                         fix_unicode=True,  # fix various unicode errors
                         to_ascii=True,  # transliterate to closest ASCII representation
                         lower=True,  # lowercase text
                         no_line_breaks=True,  # fully strip line breaks as opposed to only normalizing them
                         no_urls=True,  # replace all URLs with a special token
                         no_emails=True,  # replace all email addresses with a special token
                         no_phone_numbers=True,  # replace all phone numbers with a special token
                         no_numbers=False,  # replace all numbers with a special token
                         no_digits=False,  # replace all digits with a special token
                         no_currency_symbols=True,  # replace all currency symbols with a special token
                         no_punct=True,  # remove punctuations
                         replace_with_punct="",  # instead of removing punctuations you may replace them
                         replace_with_url="<URL>",
                         replace_with_email="<EMAIL>",
                         replace_with_phone_number="<PHONE>",
                         replace_with_number="<NUM>",
                         replace_with_digit="0",
                         replace_with_currency_symbol="<CUR>",
                         lang="en"  # set to 'de' for German special handling
                         )

    return cleaned_text


def beautify_filename(filename, num_words=20, start_reverse=False,
                      word_separator="_"):
    # takes a filename stored as text, removes extension, separates into X words ...
    # and returns a nice filename with the words separateed by
    # useful for when you are reading files, doing things to them, and making new files

    filename = str(filename)
    index_file_Ext = filename.rfind('.')
    current_name = str(filename)[:index_file_Ext]  # get rid of extension
    clean_name = cleantxt_wrap(current_name)  # wrapper with custom defs
    file_words = wordninja.split(clean_name)
    # splits concatenated text into a list of words based on common word freq
    if len(file_words) <= num_words:
        num_words = len(file_words)

    if start_reverse:
        t_file_words = file_words[-num_words:]
    else:
        t_file_words = file_words[:num_words]

    pretty_name = word_separator.join(t_file_words)  # see function argument

    # NOTE IT DOES NOT RETURN THE EXTENSION
    return pretty_name[: (len(pretty_name) - 1)]  # there is a space always at the end, so -1


def get_overviews_rasterio(input_path, output_path):
    factors = [2, 4, 8, 16]

    path = shutil.copy(input_path, output_path)
    dst = rasterio.open(path, 'r+')
    dst.build_overviews(factors, Resampling.average)
    dst.update_tags(ns='rio_overview', resampling='average')
    dst.close()


def interpret_color_2(input_path, output_path, verbose=False):
    src = rasterio.open(input_path)
    profile = src.profile
    profile['photometric'] = "RGB"
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(src.read())
    if verbose: print("finished - ", datetime.now())


def interpret_color_3(input_path, tif_filename, output_path, verbose=False):
    out_base = beautify_filename(tif_filename)

    src = rasterio.open(join(input_path, tif_filename))
    profile = src.profile
    profile['photometric'] = "RGB"

    converted_loc = join(output_path, out_base + ".tif")
    with rasterio.open(converted_loc, 'w', **profile) as dst:
        dst.write(src.read())
    dst2 = rasterio.open(converted_loc)
    ax = show(dst2, adjust='linear')
    # ax
    plt.savefig(join(output_path, out_base + ".png"))
    if verbose: print("finished - ", datetime.now())


def rasterio_2(input_path, tif_filename, output_path, verbose=False):
    out_base = beautify_filename(tif_file) + "converted_nr_{}_".format(index_pos)

    with rasterio.open(join(input_path, tif_filename)) as src:
        print(f"\nnew profile: {pp.pformat(src.profile)}\n")
        profile = src.profile
        profile['photometric'] = "RGB"
        profile['interleave'] = 'band'
        profile['blockxsize'] = 256
        profile['blockysize'] = 256
        profile['compress'] = 'lzw'
        profile['nodata'] = 0
        profile['dtype'] = uint8
        #
        # change the driver name from GTiff to PNG
        #
        # profile['driver'] = 'PNG'
        # #
        # # pathlib makes it easy to add a new suffix to a
        # # filename
        # #
        # png_filename = out_base + ".png"
        raster = src.read()
        # with rasterio.open(join(output_path, png_filename), 'w', **profile) as dst:
        #     dst.write(raster)
        #
        # now do jpeg
        #
        profile['driver'] = 'JPEG'
        profile['count'] = 3
        jpeg_filename = out_base + '.jpeg'
        with rasterio.open(join(output_path, jpeg_filename), 'w', **profile) as dst:
            dst.write(raster)


# ----------------------------------------------------------------------------

# load files
files_to_munch = natsorted([f for f in listdir(tif_dir_path) if isfile(os.path.join(tif_dir_path, f))])
total_files_1 = len(files_to_munch)
removed_count_1 = 0
approved_files = []
# remove non-tif_image files
for prefile in files_to_munch:
    if prefile.endswith(".tif"):
        approved_files.append(prefile)
    else:
        files_to_munch.remove(prefile)
        removed_count_1 += 1

print("out of {0:3d} file(s) originally in the folder, ".format(total_files_1),
      "{0:3d} non-tif_image files were removed".format(removed_count_1))
print('\n {0:3d} tif_image file(s) in folder will be transcribed.'.format(len(approved_files)))
pp.pprint(approved_files)

# ----------------------------------------------------------------------------

# loop
st = time.time()
for tif_file in tqdm(approved_files, total=len(approved_files),
                     desc="Resizing tif_images - v2"):
    index_pos = approved_files.index(tif_file)
    out_name = beautify_filename(tif_file) + "converted_nr_{}_".format(index_pos) + ".tif"
    this_input_path = join(tif_dir_path, tif_file)
    this_output_path = join(output_path_full, out_name)

    interpret_color_3(tif_dir_path, tif_file, output_path_full)

rt = round((time.time() - st) / 60, 2)
print("\n\nfinished converting all tif_images - ", datetime.now())
print("Converted {} tif_images in {} minutes".format(len(approved_files), rt))
print("they are located in: \n", output_path_full)
