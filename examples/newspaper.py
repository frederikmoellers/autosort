import logging
import pathlib
import re
import subprocess

from typing import Dict, Optional
from sorters import Sorter


class NewspaperInvoice(Sorter):
    def __init__(self, logger: logging.Logger):
        Sorter.__init__(self, logger)
        self.re = re.compile(r'INVOICE(?P<number>\d{10})_\.pdf')

    def sort(self, path: pathlib.Path) -> Optional[pathlib.PurePath]:
        data: Dict[str, str]
        match: Optional[re.Match] = self.re.match(path.name)
        if not match:
            self.logger.debug("{}: No match.".format(self.__class__.__name__))
            return None
        # check sender
        sender: str = subprocess.check_output(
            ["pdftotext", "-f", "1", "-l", "1", "-x", "54", "-y", "155", "-W", "160", "-H", "15", str(path.resolve()), "-"]
        ).decode().strip()
        if sender != "Newspaper Inc. 12345 Megacity":
            return None
        # Just move it into the directory, but don't rename the file
        return pathlib.PurePath(
            "Newspaper/Invoices/{filename}".format(filename=path.name))