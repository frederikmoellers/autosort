import logging
import pathlib
import re
import subprocess

from typing import Dict, Optional
from sorters import Sorter


class NurseryInvoice(Sorter):
    def __init__(self, logger: logging.Logger):
        Sorter.__init__(self, logger)
        self.re = re.compile(r'Invoice (?P<month>\d{2})-(?P<year>\d{4})\.pdf')

    def sort(self, path: pathlib.Path) -> Optional[pathlib.PurePath]:
        data: Dict[str, str]
        match: Optional[re.Match] = self.re.match(path.name)
        if not match:
            self.logger.debug("{}: No match.".format(self.__class__.__name__))
            return None
        pdf_subject: str = subprocess.check_output(
            ["pdftotext", "-f", "1", "-l", "1", "-x", "53", "-y", "298", "-W", "155", "-H", "84", str(path.resolve()), "-"]
        ).decode().strip()
        if pdf_subject != "Nursery XYZ\nFirstname Lastname\n\nINVOICE":
            return None
        data = {
            "month": match.group("month"),
            "year": match.group("year"),
        }
        return pathlib.PurePath(
            "Kids/Firstname/Nursery/Invoices/{data[year]}-{data[month]}.pdf".format(data=data))