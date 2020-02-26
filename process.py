import argparse
import json
import logging
import os

import bson
import yaml

JSON_EXT = ".json"
MIN_JSON_EXT = ".min.json"
BSON_EXT = ".bson"
YAML_EXT = ".yaml"
TXT_EXT = ".txt"

EXCLUDE_DIRS = [".cache", "tmp"]

ARGPARSER = argparse.ArgumentParser(description="Run the mcdata update utility.")
ARGPARSER.add_argument("--inpath", help="The path to read the generated data from.")
ARGPARSER.add_argument("--outpath", help="The path to write the processed output to.")
ARGPARSER.add_argument("--log", help="The logging level.", default=logging.WARNING)
ARGS = ARGPARSER.parse_args()

logging.basicConfig(level=ARGS.log)
LOG = logging.getLogger(__name__)


def ensure_dir(dirname: str):
    if not os.path.exists(dirname):
        LOG.debug(f"Creating missing directory: {dirname}")
        os.makedirs(dirname)


def write_json(data: dict, dirname: str, filename: str):
    subdirname = os.path.join(dirname, filename)
    ensure_dir(subdirname)
    filepath = os.path.join(subdirname, filename + JSON_EXT)
    with open(filepath, "w") as fp:
        LOG.debug(f"Writing JSON file: {filepath}")
        json.dump(data, fp, indent=2)


def write_min_json(data: dict, dirname: str, filename: str):
    subdirname = os.path.join(dirname, filename)
    ensure_dir(subdirname)
    filepath = os.path.join(subdirname, filename + MIN_JSON_EXT)
    with open(filepath, "w") as fp:
        LOG.debug(f"Writing minified JSON file: {filepath}")
        json.dump(data, fp, separators=(",", ":"))


def write_bson(data: dict, dirname: str, filename: str):
    subdirname = os.path.join(dirname, filename)
    ensure_dir(subdirname)
    filepath = os.path.join(subdirname, filename + BSON_EXT)
    with open(filepath, "wb") as fp:
        LOG.debug(f"Writing BSON file: {filepath}")
        fp.write(bson.dumps(data))


def write_yaml(data: dict, dirname: str, filename: str):
    subdirname = os.path.join(dirname, filename)
    ensure_dir(subdirname)
    filepath = os.path.join(subdirname, filename + YAML_EXT)
    with open(filepath, "w") as fp:
        LOG.debug(f"Writing YAML file: {filepath}")
        yaml.dump(data, fp)


def write_txt(data: list, dirname: str, filename: str):
    subdirname = os.path.join(dirname, filename)
    ensure_dir(subdirname)
    filepath = os.path.join(subdirname, filename + TXT_EXT)
    with open(filepath, "w") as fp:
        LOG.debug(f"Writing TXT file: {filepath}")
        fp.write('\n'.join(data))


def convert_file(in_dirname: str, in_filename: str, out_dirname: str):
    out_filename = in_filename[: -len(JSON_EXT)]
    in_filepath = os.path.join(in_dirname, in_filename)
    with open(in_filepath) as fp:
        LOG.debug(f"Reading original file: {in_filepath}")
        data = json.load(fp)
    write_min_json(data, out_dirname, out_filename)
    write_bson(data, out_dirname, out_filename)
    write_yaml(data, out_dirname, out_filename)


def convert_files(inparts: tuple, outparts: tuple):
    # create minified versions of all original files
    inpath = os.path.join(*inparts)
    for dirname, subdirnames, filenames in os.walk(inpath):
        LOG.info(f"Reading directory: {dirname}")
        # ignore things like cache and tmp folder
        subdirnames[:] = [d for d in subdirnames if d not in EXCLUDE_DIRS]
        # don't include the root "generated" folder in the output
        dirparts = dirname.split(os.path.sep)[1:]
        LOG.debug(f"Directory path components: {dirparts}")
        out_dirname = os.path.join(*outparts, *dirparts)
        LOG.debug(f"Using output directory: {out_dirname}")
        # process each file
        for filename in filenames:
            if filename.endswith(JSON_EXT):
                convert_file(dirname, filename, out_dirname)


def process_registry(registry: dict, dirname: str, filename: str):
    entries = registry["entries"]
    values = list(entries.keys())
    data = {"values": values}
    write_json(data, dirname, filename)
    write_min_json(data, dirname, filename)
    write_bson(data, dirname, filename)
    write_yaml(data, dirname, filename)
    write_txt(values, dirname, filename)


def split_registries(inparts: tuple, outparts: tuple):
    # split the registries into multiple files
    registries_subdir = os.path.join(*outparts, "reports", "registries")
    registries_path = os.path.join(*inparts, "reports", "registries.json")
    LOG.info(f"Reading registries from: {registries_path}")
    with open(registries_path) as registries_fp:
        registries_data = json.load(registries_fp)
    # process each registry
    for reg_name, registry in registries_data.items():
        reg_entries = registry["entries"]
        LOG.info(f"Found {len(reg_entries)} entries for registry: {reg_name}")
        reg_shortname = reg_name.split(":")[1]
        process_registry(registry, registries_subdir, reg_shortname)


def process(inparts: tuple, outparts: tuple):
    print("Converting files...")
    convert_files(inparts, outparts)
    print("Splitting registries...")
    split_registries(inparts, outparts)
    print('Done!')


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
