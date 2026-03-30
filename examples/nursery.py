import lib.pdf
import logging
import pathlib
import re

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
        pdf: lib.pdf.PDF = lib.pdf.PDF(path)
        pdf_subject: str = pdf.get_text(1, 53, 298, 323, 84)
        if pdf_subject not in {
            "Nursery XYZ\nFirstname Lastname\n\nINVOICE",
            "Nursery XYZ\nFirstname\n\nINVOICE",
            "Nursery XYZ, Address\nFirstname Lastname\n\nINVOICE",
        }:
            self.logger.debug("'{}'".format(pdf_subject))
        if pdf_subject != "Nursery XYZ\nFirstname Lastname\n\nINVOICE":
            return None
        data = {
            "month": match.group("month"),
            "year": match.group("year"),
        }
        return pathlib.PurePath(
            "Kids/Firstname/Nursery/Invoices/{data[year]}-{data[month]}.pdf".format(data=data))