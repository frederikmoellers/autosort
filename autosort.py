#!/usr/bin/env python3

import argparse
import importlib.util
import inspect
import logging
import logging.config
import pathlib
import pkgutil
import platform
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
        # Sorter does not handle this file
        if not sorter_result:
            continue
        # Sorter returns a single target path
        elif isinstance(sorter_result, pathlib.PurePath):
            target_path = BASE_DIR / sorter_result
            print("'{}' → '{}' ".format(
                path,
                termcolor.colored(target_path, "red") if target_path.exists() else termcolor.colored(target_path, "green"),
            ), end="")
        # Sorter returns a list of page ranges and respective target paths
        elif isinstance(sorter_result, list):
            # TODO: What do we do if multiple page ranges point to the same target_path? We should highlight this.
            for page_range, target_path in sorter_result:
                target_path = BASE_DIR / target_path
                print("'{}:{}' → '{}' ".format(
                    path,
                    page_range,
                    termcolor.colored(target_path, "red") if target_path.exists() else termcolor.colored(target_path, "green"),
                ))
        while True:
            user_input = input("(Y/n/v/?)?")
            if user_input in {"Y", "y", "Z", "z", ""}:
                if isinstance(sorter_result, pathlib.PurePath):
                    LOG.debug("Moving '{}' to '{}'".format(path, target_path))
                    path.rename(target_path)
                    break
                elif isinstance(sorter_result, list):
                    # TODO: If the page ranges don't cover all pages, we shouldn't remove the source file!
                    for page_range, target_path in sorter_result:
                        target_path = BASE_DIR / target_path
                        print("'Moving {}:{}' to '{}' ".format(
                            path,
                            page_range,
                            target_path,
                        ))
                        LOG.debug("Calling: {}".format(["pdftk", path, "cat", page_range, "output", target_path]))
                        subprocess.run(["pdftk", path, "cat", page_range, "output", target_path], check=True)
                    path.unlink()
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
                if isinstance(target_path, pathlib.PurePath) and target_path.exists():
                    view_file(target_path)
                elif isinstance(sorter_result, list):
                    for page_range, target_path in sorter_result:
                        target_path = BASE_DIR / target_path
                        view_file(target_path)
                view_file(path)
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


def view_file(path: pathlib.Path):
    """
    Opens a file in the operating system's default viewer.
    """
    operating_system = platform.system()
    if operating_system == "Darwin":
        command = "open"
    elif operating_system == "Linux":
        command = "xdg-open"
    else:
        raise Exception("Cannot view file '{}'! Unknown operating system '{}'".format(path, operating_system))
    subprocess.Popen([command, path])



BASE_DIR: pathlib.Path
LOG: logging.Logger = configure_logger()
SORTERS: Set[sorters.Sorter] = set()
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

    # automatically load all available parser modules
    LOG.debug("Looking for sorters in '{}'".format(sorters.__path__))
    for module_finder, name, is_pkg in pkgutil.walk_packages(sorters.__path__):
        LOG.debug("Found sorter module '{}'".format(name))
        spec = module_finder.find_spec(name)
        sorter_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sorter_module)
        for classname, classobj in inspect.getmembers(sorter_module):
            if inspect.isclass(classobj) and issubclass(classobj, sorters.Sorter) and classobj is not sorters.Sorter:
                sorter_obj = classobj(LOG)
                LOG.debug("Added sorter: {}".format(sorter_obj))
                SORTERS.add(sorter_obj)

    # sort paths given by arguments
    for path in arguments.paths:
        # if path is a directory, call autosort for all files within
        autosort(path)
