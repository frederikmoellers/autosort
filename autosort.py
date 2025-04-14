#!/usr/bin/env python3

import argparse
import inspect
import logging
import logging.config
import pathlib
import pkgutil
import subprocess

import sorters
import sys
import termcolor

from typing import Set, Optional


def autosort(path: pathlib.Path):
    """
    Automatically sort a document
    :param path: Path to a file or a directory containing files to be sorted
    :return: None
    """
    # check if path exists at all
    if not path.exists():
        raise FileNotFoundError("Path '{}' does not exist!".format(path))
    # handle directories recursively
    if path.is_dir():
        LOG.debug("Recursively sorting directory '{}'".format(path))
        for dir_entry in path.glob("*"):
            autosort(dir_entry)
    # do not handle this script itself
    if path.resolve() == THIS_SCRIPT:
        return
    # try sorters until one handles this file
    LOG.debug("Sorting file '{}'".format(path))
    for sorter in SORTERS:
        sorter_result = sorter.sort(path)
        if not sorter_result:
            continue
        target_path = BASE_DIR / sorter_result
        print("'{}' → '{}' ".format(
            path,
            termcolor.colored(target_path, "red") if target_path.exists() else termcolor.colored(target_path, "green"),
        ), end="")
        process1: Optional[subprocess.Popen] = None
        process2: Optional[subprocess.Popen] = None
        while True:
            user_input = input("(Y/n/v/?)?")
            if user_input in {"Y", "y", "Z", "z", ""}:
                LOG.debug("Moving '{}' to '{}'".format(path, target_path))
                path.rename(target_path)
                break
            elif user_input in {"N", "n"}:
                break
            elif user_input in {"V", "v"}:
                """
                We don't keep track of the view processes because xdg-open often immediately exits. There is no way of
                knowing whether the view process is long-running (so we should keep track and terminate it before the
                next iteration) or immediately exits (so we can discard it immediately and just call a new one in the
                next iteration). We have to rely on the user to quit the view processes when they are finished
                reviewing the files.
                """
                if(target_path.exists()):
                    subprocess.Popen(["xdg-open", target_path])
                subprocess.Popen(["xdg-open", path])
            elif user_input == "?":
                print("Y: Yes, move file\n")
                print("N: No, do not move file\n")
                print("V: View file(s)\n")
                print("?: Show this help\n")
        # TODO: Only continue to the next sorter if an action was taken?


def configure_logger() -> logging.Logger:
    """
    Configures a logger and returns it.
    :return: A logging.Logger object ready to be used for logging.
    """
    logging.config.dictConfig({
        "version": 1,
        "formatters": {
            "simple": {
                "format": '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                "datefmt": '%Y-%m-%d %H:%M:%S',
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "stream": "ext://sys.stderr",
            }
        },
        "loggers": {
            "autosort": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": "no",
            }
        },
    })
    return logging.getLogger("autosort")


BASE_DIR: pathlib.Path
LOG: logging.Logger = configure_logger()
SORTERS: Set[sorters.Sorter] = set()
# automatically load all available parser modules
for loader, name, is_pkg in pkgutil.walk_packages(sorters.__path__):
    sorter_module = loader.find_module(name).load_module(name)
    for classname, classobj in inspect.getmembers(sorter_module):
        if inspect.isclass(classobj) and issubclass(classobj, sorters.Sorter) and classobj is not sorters.Sorter:
            SORTERS.add(classobj(LOG))
THIS_SCRIPT: pathlib.Path = pathlib.Path(sys.argv[0]).resolve()


# if called as an executable script
if __name__ == "__main__":
    # parse arguments
    argument_parser = argparse.ArgumentParser(
        description="Automatically sort documents into folder structure."
    )
    argument_parser.add_argument(
        "-b", "--base_dir",
        default=pathlib.Path.home() / "Documents",
        type=pathlib.Path,
        help="Base directory where to store sorted documents",
        dest="base_dir"
    )
    argument_parser.add_argument(
        "-l", "--log-level",
        default="WARNING",
        help="Log level (DEBUG/INFO/WARNING/ERROR)",
        dest="log_level",
    )
    argument_parser.add_argument(
        "paths",
        nargs="+",
        type=pathlib.Path,
        help="Folders containing the documents to sort or the documents themselves",
        metavar="directory_or_file",
    )
    arguments = argument_parser.parse_args()
    BASE_DIR = arguments.base_dir
    LOG.setLevel(arguments.log_level)
    for path in arguments.paths:
        # if path is a directory, call autosort for all files within
        autosort(path)
