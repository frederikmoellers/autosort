import logging
import pathlib

from abc import ABC, abstractmethod
from typing import Optional


class Sorter(ABC):
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    @classmethod
    @abstractmethod
    def sort(cls, path: pathlib.Path) -> Optional[pathlib.PurePath]:
        """
        Sort
        :return:
        """