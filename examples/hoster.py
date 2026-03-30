import lib.pdf
import logging
import pathlib
import re

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
        pdf: lib.pdf.PDF = lib.pdf.PDF(path)
        # check customer number
        customer_no: str = pdf.get_text(1, 523, 209, 46, 9)
        if customer_no != "K1234567890":
            return None
        # Just move it into the directory, but don't rename the file
        return pathlib.PurePath(
            "Hoster/Invoices/{filename}".format(filename=path.name))