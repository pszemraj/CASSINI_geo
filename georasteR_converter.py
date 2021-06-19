"""
now using
https://towardsdatascience.com/reading-and-visualizing-geotiff-images-with-python-8dcca7a74510
https://github.com/GeoUtils/georaster/blob/master/georaster/georaster.py

"""

import os
import pprint as pp
import time
from datetime import datetime
from os import listdir
from os.path import join, isfile

import georaster
from osgeo import gdal
import matplotlib.pyplot as plt
import wordninja
from cleantext import clean
from natsort import natsorted
from tqdm import tqdm

tif_dir_path = str(input("Enter path to folder with geotiff files -->"))
# -----------------------------------------------------------------
output_folder_name = "georasteR_conversion"
output_path_full = os.path.join(tif_dir_path, output_folder_name)
if not os.path.isdir(output_path_full):
    os.mkdir(output_path_full)
    # make a place to store outputs if one does not exist
print("outputs will be in: \n", output_path_full)


# -----------------------------------------------------------------


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


# ----------------------------------------------------------------------------

def convert_tiff_to_png_georasters(input_path, output_path, verbose=False):
    # Use SingleBandRaster() if image has only one band
    img = georaster.MultiBandRaster(input_path)
    # img.r gives the raster in [height, width, band] format
    # band no. starts from 0
    plt.imshow(img.r[:, :, 2], interpolation='spline36')
    plt.title(os.path.basename(input_path))
    plt.savefig(output_path, bbox_inches='tight', dpi=200)

    if verbose:
        # For no. of bands and resolution
        gd_img = gdal.Open(input_path, gdal.GA_ReadOnly)
        print("\n data on rasters from gdal:")
        gd_img.RasterCount, gd_img.RasterXSize, gd_img.RasterYSize
        gd_img.GetStatistics(True, True)
        # stats about image
        img.GetStatistics(True, True)





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
                     desc="Resizing tif_images"):
    index_pos = approved_files.index(tif_file)
    out_name = beautify_filename(tif_file) + "converted_nr_{}_".format(index_pos) + ".png"
    this_input_path = join(tif_dir_path, tif_file)
    this_output_path = join(output_path_full, out_name)
    convert_tiff_to_png_georasters(this_input_path, this_output_path)

rt = round((time.time() - st) / 60, 2)
print("\n\nfinished converting all tif_images - ", datetime.now())
print("Converted {} tif_images in {} minutes".format(len(approved_files), rt))
print("they are located in: \n", output_path_full)
