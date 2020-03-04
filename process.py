import argparse
import json
import logging
import os

import yaml

JSON_EXT = ".json"
MIN_JSON_EXT = ".min.json"
YAML_EXT = ".yaml"
TXT_EXT = ".txt"

EXCLUDE_DIRS = [".cache", "tmp"]

DATA_SUBPARTS = (
    ("advancements",),
    ("loot_tables",),
    ("recipes",),
    ("tags", "blocks"),
    ("tags", "entity_types"),
    ("tags", "fluids"),
    ("tags", "items"),
)

ARGPARSER = argparse.ArgumentParser(description="Run the mcdata update utility.")
ARGPARSER.add_argument("--inpath", help="The path to read the generated data from.")
ARGPARSER.add_argument("--outpath", help="The path to write the processed output to.")
ARGPARSER.add_argument("--log", help="The logging level.", default=logging.WARNING)
ARGS = ARGPARSER.parse_args()

logging.basicConfig(level=ARGS.log)
LOG = logging.getLogger(__name__)


def prepare_filepath(dirname: str, subname: str, ext: str) -> str:
    subdirname = os.path.join(dirname, subname)
    if not os.path.exists(subdirname):
        LOG.debug(f"Creating missing directory: {subdirname}")
        os.makedirs(subdirname)
    filepath = os.path.join(subdirname, subname + ext)
    return filepath


def write_json(data: dict, dirname: str, subname: str):
    filepath = prepare_filepath(dirname, subname, JSON_EXT)
    with open(filepath, "w") as fp:
        LOG.debug(f"Writing JSON file: {filepath}")
        json.dump(data, fp, indent=2)


def write_min_json(data: dict, dirname: str, subname: str):
    filepath = prepare_filepath(dirname, subname, MIN_JSON_EXT)
    with open(filepath, "w") as fp:
        LOG.debug(f"Writing minified JSON file: {filepath}")
        json.dump(data, fp, separators=(",", ":"))


def write_yaml(data: dict, dirname: str, subname: str):
    filepath = prepare_filepath(dirname, subname, YAML_EXT)
    with open(filepath, "w") as fp:
        LOG.debug(f"Writing YAML file: {filepath}")
        yaml.dump(data, fp)


def write_txt(data: list, dirname: str, subname: str):
    filepath = prepare_filepath(dirname, subname, TXT_EXT)
    with open(filepath, "w") as fp:
        LOG.debug(f"Writing TXT file: {filepath}")
        fp.write("\n".join(data))


def convert_file(in_dirname: str, in_filename: str, out_dirname: str):
    in_filepath = os.path.join(in_dirname, in_filename)
    with open(in_filepath) as fp:
        LOG.debug(f"Reading original file: {in_filepath}")
        data = json.load(fp)
    out_filename = in_filename[: -len(JSON_EXT)]
    write_min_json(data, out_dirname, out_filename)
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


def process_registry(registry: dict, dirname: str, shortname: str):
    entries = registry["entries"]
    values = list(entries.keys())
    data = {"values": values}
    write_json(data, dirname, shortname)
    write_min_json(data, dirname, shortname)
    write_yaml(data, dirname, shortname)
    write_txt(values, dirname, shortname)


def split_registries(inparts: tuple, outparts: tuple):
    # split the registries into multiple files
    registries_path = os.path.join(*inparts, "reports", "registries.json")
    LOG.info(f"Reading registries from: {registries_path}")
    with open(registries_path) as registries_fp:
        registries_data = json.load(registries_fp)
    # process each registry
    registries_outdir = os.path.join(*outparts, "reports", "registries")
    for reg_name, registry in registries_data.items():
        reg_entries = registry["entries"]
        LOG.info(f"Found {len(reg_entries)} entries for registry: {reg_name}")
        reg_shortname = reg_name.split(":")[1]
        process_registry(registry, registries_outdir, reg_shortname)


def summarize_data(inparts: tuple, outparts: tuple):
    # compile namespaced id reports for data root folders
    data_path = os.path.join(*inparts, "data")
    for namespace in os.listdir(data_path):
        namespace_root = os.path.join(data_path, namespace)
        summaries = {}
        for data_subparts in DATA_SUBPARTS:
            resource_ids = []
            summary = {'values': resource_ids}
            # recursively construct data structure for namespace summary
            sub_summaries = summaries
            for subpart in data_subparts[:-1]:
                if subpart not in sub_summaries:
                    sub_summaries[subpart] = {}
                sub_summaries = sub_summaries[subpart]
            sub_summaries[data_subparts[-1]] = resource_ids
            # process individual summaries
            namespace_subdir = os.path.join(*data_subparts)
            namespace_data_root = os.path.join(namespace_root, namespace_subdir)
            for dirname, subdirnames, filenames in os.walk(namespace_data_root):
                LOG.info(f"Reading directory: {dirname}")
                subdirnames[:] = [d for d in subdirnames if d not in EXCLUDE_DIRS]
                for filename in filenames:
                    resource_header_len = len(namespace_data_root) + len(os.path.sep)
                    resource_dir = dirname[resource_header_len:]
                    resource_dir_parts = (
                        resource_dir.split(os.path.sep) if resource_dir else []
                    )
                    filename_parts = filename.split(".")
                    filename_parts_without_ext = filename_parts[:-1]
                    filename_without_ext = ".".join(filename_parts_without_ext)
                    resource_name = "/".join(
                        (*resource_dir_parts, filename_without_ext)
                    )
                    resource_id = f"{namespace}:{resource_name}"
                    resource_ids.append(resource_id)
            summary_out_dir = os.path.join(*outparts, 'data', namespace, *data_subparts[:-1])
            write_json(summary, summary_out_dir, data_subparts[-1])
            write_min_json(summary, summary_out_dir, data_subparts[-1])
            write_yaml(summary, summary_out_dir, data_subparts[-1])
            write_txt(resource_ids, summary_out_dir, data_subparts[-1])
        summaries_out_dir = os.path.join(*outparts, 'data')
        write_json(summaries, summaries_out_dir, namespace)
        write_min_json(summaries, summaries_out_dir, namespace)
        write_yaml(summaries, summaries_out_dir, namespace)


def process(inparts: tuple, outparts: tuple):
    print("Converting files...")
    convert_files(inparts, outparts)
    print("Splitting registries...")
    split_registries(inparts, outparts)
    print("Summarizing data...")
    summarize_data(inparts, outparts)
    print("Done!")


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
