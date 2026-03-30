import lib.pdf
import logging
import pathlib
import re

from lib.calendar import month_names
from typing import Any, Dict, Optional
from sorters import Sorter


class MobileInvoice(Sorter):
    def __init__(self, logger: logging.Logger):
        Sorter.__init__(self, logger)
        self.re = re.compile(r'Invoice_((?P<month_off>\d{2})_(?P<year_off>\d{4})_)?(?P<number>(R\d{10}|\d{14}))\.pdf')

    @staticmethod
    def get_customer_account_no(file: lib.pdf.PDF) -> Optional[str]:
        customer_account_no: str = file.get_text(1, 505, 182, 56, 14)
        if customer_account_no:
            return customer_account_no
        customer_account_no = file.get_text(1, 503, 180, 59, 13)
        return customer_account_no

    @staticmethod
    def get_date(file: lib.pdf.PDF) -> Dict[str, int]:
        # try to extract from PDF
        month_str: str
        year_str: str
        month_str, year_str = file.get_text(1, 287, 260, 150, 14).split(" ")
        month: int = month_names["de"].index(month_str) + 1
        year: int = int(year_str)
        return {"month": month, "year": year}

    def sort(self, path: pathlib.Path) -> Optional[pathlib.PurePath]:
        data: Dict[str, Any]
        match: Optional[re.Match] = self.re.match(path.name)
        if not match:
            self.logger.debug("{}: No match.".format(self.__class__.__name__))
            return None
        pdf: lib.pdf.PDF = lib.pdf.PDF(path)
        # check customer number
        customer_account_no = self.get_customer_account_no(pdf)
        if customer_account_no != "12 3456 7890":
            self.logger.debug("{}: Invalid customer account number: {}".format(self.__class__.__name__, customer_account_no))
            return None
        data = self.get_date(pdf)
        if "month" not in data or "year" not in data:
            return None
        return pathlib.PurePath(
            "Telephone/Invoices/{year:04d}-{month:02d}.pdf".format(**data))