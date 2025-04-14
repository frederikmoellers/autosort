import logging
import pathlib
import re
import subprocess

from typing import Dict, Optional
from sorters import Sorter


class HosterInvoice(Sorter):
    def __init__(self, logger: logging.Logger):
        Sorter.__init__(self, logger)
        self.re = re.compile(r'Hoster_(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})_(?P<number>(R\d{10}|\d{12}))\.pdf')

    def sort(self, path: pathlib.Path) -> Optional[pathlib.PurePath]:
        data: Dict[str, str]
        match: Optional[re.Match] = self.re.match(path.name)
        if not match:
            self.logger.debug("{}: No match.".format(self.__class__.__name__))
            return None
        # check customer number
        customer_no: str = subprocess.check_output(
            ["pdftotext", "-f", "1", "-l", "1", "-x", "523", "-y", "209", "-W", "46", "-H", "9", str(path.resolve()), "-"]
        ).decode().strip()
        if customer_no != "K1234567890":
            return None
        # Just move it into the directory, but don't rename the file
        return pathlib.PurePath(
            "Hoster/Invoices/{filename}".format(filename=path.name))