import logging
import pathlib

from abc import ABC, abstractmethod
from typing import Optional, Union, Tuple


class Sorter(ABC):
    def __init__(self, logger: logging.Logger):
        """
        Base constructor, saves the logger instance
        :param logger:
        """
        self.logger = logger

    @classmethod
    @abstractmethod
    def sort(cls, path: pathlib.Path) -> Optional[Union[pathlib.PurePath, Tuple[str, pathlib.PurePath]]]:
        """
        Determine where the file should be moved to.
        :return: Either of the following:
                 `None`: If this sorter does not know how to handle the file or where to move it to.
                 A `pathlib.PurePath`: The path to the file that should be moved to.
                 A list of tuples `(str, pathlib.PurePath)`: The first element is a page range to be given to `pdftk`.
                                                             The second element is the path to where that page range
                                                             should be moved to.
        """