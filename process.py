import argparse
import json
import logging
import os

import bson

JSON_EXT = ".json"
MIN_EXT = ".min.json"
BIN_EXT = ".bson"

EXCLUDE_DIRS = [".cache", "tmp"]

ARGPARSER = argparse.ArgumentParser(description="Run the mcdata update utility.")
ARGPARSER.add_argument("--inpath", help="The path to read the generated data from.")
ARGPARSER.add_argument("--outpath", help="The path to write the processed output to.")
ARGPARSER.add_argument("--log", help="The logging level.", default=logging.INFO)
ARGS = ARGPARSER.parse_args()

logging.basicConfig(level=ARGS.log)
LOG = logging.getLogger(__name__)


def process_file(old_dirname: str, old_filename: str, new_dirname: str):
    old_filepath = os.path.join(old_dirname, old_filename)
    # read the original file
    with open(old_filepath) as fp:
        LOG.debug(f"Reading original file: {old_filepath}")
        data = json.load(fp)
    # write a minified version
    min_filename = old_filename[: -len(JSON_EXT)] + MIN_EXT
    min_filepath = os.path.join(new_dirname, min_filename)
    with open(min_filepath, "w") as min_fp:
        LOG.debug(f"Writing minified file: {min_filepath}")
        json.dump(data, min_fp, separators=(",", ":"))
    # write a binary version
    bin_filename = old_filename[: -len(JSON_EXT)] + BIN_EXT
    bin_filepath = os.path.join(new_dirname, bin_filename)
    with open(bin_filepath, "wb") as bin_fp:
        LOG.debug(f"Writing binary file: {bin_filepath}")
        bin_fp.write(bson.dumps(data))


def make_minified(inparts: tuple, outparts: tuple):
    # create minified versions of all original files
    inpath = os.path.join(*inparts)
    for dirname, subdirnames, filenames in os.walk(inpath):
        LOG.info(f"Checking directory: {dirname}")
        # ignore things like cache and tmp folder
        subdirnames[:] = [d for d in subdirnames if d not in EXCLUDE_DIRS]
        # skip the "generated" folder
        dirparts = dirname.split(os.path.sep)[1:]
        LOG.debug(f"Directory path components: {dirparts}")
        out_dirname = os.path.join(*outparts, *dirparts)
        LOG.debug(f"Using output directory: {out_dirname}")
        # make sure the subfolder exists
        if not os.path.exists(out_dirname):
            LOG.debug(f"Creating missing output directory: {out_dirname}")
            os.makedirs(out_dirname)
        # process each file
        for filename in filenames:
            if filename.endswith(JSON_EXT):
                process_file(dirname, filename, out_dirname)


def process(inparts: tuple, outparts: tuple):
    make_minified(inparts, outparts)


def run():
    inpath = os.path.relpath(
        ARGS.inpath or input("Where should the generated data be read from?: ")
    )
    outpath = ARGS.outpath or input(
        "Where should the processed output be written to?: "
    )

    inparts = inpath.split(os.path.sep)
    outparts = outpath.split(os.path.sep)

    LOG.debug(f"Input path components: {inparts}")
    LOG.debug(f"Output path components: {outparts}")

    actual_inpath = os.path.join(*inparts)
    actual_outpath = os.path.join(*outparts)

    LOG.info(f"Using input path: {actual_inpath}")
    LOG.info(f"Using output path: {actual_outpath}")

    if not os.path.exists(actual_inpath):
        print(
            "[Error] The provided path for generated data does not exist:",
            actual_inpath,
        )
    elif os.path.exists(actual_outpath):
        print(
            "[Error] The provided path for processed output already exists;"
            + " it should be deleted before proceeding:",
            actual_outpath,
        )
    else:
        process(inparts, outparts)


run()
