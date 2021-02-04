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
    ("tags", "game_events"),
    ("tags", "items"),
)

REPORT_SUBPARTS = (("biomes",),)

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
    filename = "data"
    filepath = os.path.join(subdirname, filename + ext)
    return filepath


def write_json(data: dict, dirname: str, subname: str):
    filepath = prepare_filepath(dirname, subname, JSON_EXT)
    LOG.debug(f"Writing JSON file: {filepath}")
    with open(filepath, "w") as fp:
        json.dump(data, fp, indent=2, sort_keys=True)


def write_min_json(data: dict, dirname: str, subname: str):
    filepath = prepare_filepath(dirname, subname, MIN_JSON_EXT)
    LOG.debug(f"Writing minified JSON file: {filepath}")
    with open(filepath, "w") as fp:
        json.dump(data, fp, separators=(",", ":"), sort_keys=True)


def write_yaml(data: dict, dirname: str, subname: str):
    filepath = prepare_filepath(dirname, subname, YAML_EXT)
    LOG.debug(f"Writing YAML file: {filepath}")
    with open(filepath, "w") as fp:
        yaml.safe_dump(data, fp, sort_keys=True)


def write_txt(data: list, dirname: str, subname: str):
    filepath = prepare_filepath(dirname, subname, TXT_EXT)
    LOG.debug(f"Writing TXT file: {filepath}")
    with open(filepath, "w") as fp:
        fp.write("\n".join(data))


def process_original(in_dirname: str, in_filename: str, out_dirname: str):
    in_filepath = os.path.join(in_dirname, in_filename)
    LOG.debug(f"Reading original file for processing: {in_filepath}")
    with open(in_filepath) as fp:
        data = json.load(fp)
    out_filename = in_filename[: -len(JSON_EXT)]
    write_json(data, out_dirname, out_filename)
    write_min_json(data, out_dirname, out_filename)
    write_yaml(data, out_dirname, out_filename)


def process_originals(inparts: tuple, outparts: tuple):
    # create processed versions of original files
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
                process_original(dirname, filename, out_dirname)


def process_registry(registry: dict, dirname: str, shortname: str):
    entries = registry["entries"]
    values = sorted(list(entries.keys()))
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


def simplify_blocks(inparts: tuple, outparts: tuple):
    blocks_path = os.path.join(*inparts, "reports", "blocks.json")
    LOG.info(f"Reading block from: {blocks_path}")
    with open(blocks_path) as blocks_fp:
        blocks_data = json.load(blocks_fp)
    blocks_outdir = os.path.join(*outparts, "reports", "blocks")
    data = {}
    for block_name, block_data in blocks_data.items():
        data[block_name] = {
            "properties": block_data.get("properties", {}),
            "default": next(
                filter(lambda s: s.get("default", False), block_data["states"])
            ).get("properties", {}),
        }
    write_json(data, blocks_outdir, "simplified")
    write_min_json(data, blocks_outdir, "simplified")
    write_yaml(data, blocks_outdir, "simplified")


def summarize_reports(inparts: tuple, outparts: tuple):
    # assume namespace is `minecraft` for now
    namespace = "minecraft"
    # compile namespaced id reports for report root folders
    reports_path = os.path.join(*inparts, "reports")
    for report_subparts in REPORT_SUBPARTS:
        unsorted_resource_ids = []
        # process individual summaries
        namespace_subdir = os.path.join(reports_path, *report_subparts)
        for dirname, subdirnames, filenames in os.walk(namespace_subdir):
            LOG.info(f"Reading directory: {dirname}")
            subdirnames[:] = [d for d in subdirnames if d not in EXCLUDE_DIRS]
            for filename in filenames:
                resource_header_len = len(namespace_subdir) + len(os.path.sep)
                resource_dir = dirname[resource_header_len:]
                resource_dir_parts = (
                    resource_dir.split(os.path.sep) if resource_dir else []
                )
                filename_parts = filename.split(".")
                filename_parts_without_ext = filename_parts[:-1]
                filename_without_ext = ".".join(filename_parts_without_ext)
                resource_name = "/".join((*resource_dir_parts, filename_without_ext))
                resource_id = f"{namespace}:{resource_name}"
                unsorted_resource_ids.append(resource_id)
        sorted_resource_ids = sorted(unsorted_resource_ids)
        summary = {"values": sorted_resource_ids}
        summary_out_dir = os.path.join(*outparts, "reports", *report_subparts[:-1])
        write_json(summary, summary_out_dir, report_subparts[-1])
        write_min_json(summary, summary_out_dir, report_subparts[-1])
        write_yaml(summary, summary_out_dir, report_subparts[-1])
        write_txt(sorted_resource_ids, summary_out_dir, report_subparts[-1])


def summarize_data(inparts: tuple, outparts: tuple):
    # compile namespaced id reports for data root folders
    data_path = os.path.join(*inparts, "data")
    for namespace in os.listdir(data_path):
        namespace_root = os.path.join(data_path, namespace)
        summaries = {}
        for data_subparts in DATA_SUBPARTS:
            unsorted_resource_ids = []
            # recursively construct data structure for namespace summary
            sub_summaries = summaries
            for subpart in data_subparts[:-1]:
                if subpart not in sub_summaries:
                    sub_summaries[subpart] = {}
                sub_summaries = sub_summaries[subpart]
            sub_summaries[data_subparts[-1]] = unsorted_resource_ids
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
                    unsorted_resource_ids.append(resource_id)
            summary_out_dir = os.path.join(
                *outparts, "data", namespace, *data_subparts[:-1]
            )
            sorted_resource_ids = sorted(unsorted_resource_ids)
            summary = {"values": sorted_resource_ids}
            write_json(summary, summary_out_dir, data_subparts[-1])
            write_min_json(summary, summary_out_dir, data_subparts[-1])
            write_yaml(summary, summary_out_dir, data_subparts[-1])
            write_txt(sorted_resource_ids, summary_out_dir, data_subparts[-1])
        summaries_out_dir = os.path.join(*outparts, "data")
        write_json(summaries, summaries_out_dir, namespace)
        write_min_json(summaries, summaries_out_dir, namespace)
        write_yaml(summaries, summaries_out_dir, namespace)


def process(inparts: tuple, outparts: tuple):
    print("Processing originals...")
    process_originals(inparts, outparts)
    print("Splitting registries...")
    split_registries(inparts, outparts)
    print("Simplifying blocks...")
    simplify_blocks(inparts, outparts)
    print("Summarizing reports...")
    summarize_reports(inparts, outparts)
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
