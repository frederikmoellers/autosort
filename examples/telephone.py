import logging
import pathlib
import re
import subprocess

from typing import Any, Dict, Optional
from sorters import Sorter


class MobileInvoice(Sorter):
    def __init__(self, logger: logging.Logger):
        Sorter.__init__(self, logger)
        self.re = re.compile(r'Invoice_((?P<month_off>\d{2})_(?P<year_off>\d{4})_)?(?P<number>(R\d{10}|\d{14}))\.pdf')

    def get_customer_account_no(self, file: pathlib.Path) -> Optional[str]:
        customer_account_no: str = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "1", "-x", "505", "-y", "182", "-W", "56", "-H", "14", str(file.resolve()), "-"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ).stdout.decode().strip()
        if customer_account_no:
            return customer_account_no
        customer_account_no: str = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "1", "-x", "503", "-y", "170", "-W", "59", "-H", "13",
             str(file.resolve()), "-"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ).stdout.decode().strip()
        return customer_account_no

    def get_date(self, file: pathlib.Path) -> Dict[str, int]:
        # try to extract from PDF
        month_year: str = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "1", "-x", "287", "-y", "260", "-W", "150", "-H", "14", str(file.resolve()), "-"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ).stdout.decode().strip()
        month, year = month_year.split(" ")
        date = {
            "month": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"].index(month) + 1,
            "year": int(year),
        }
        # TODO: check if date['month'] is 1<=x<=12 and year is in range(2000, 2100), if not use the filename
        # Note that dates in filename are off by one month
        return date

    def sort(self, path: pathlib.Path) -> Optional[pathlib.PurePath]:
        data: Dict[str, Any]
        match: Optional[re.Match] = self.re.match(path.name)
        if not match:
            self.logger.debug("{}: No match.".format(self.__class__.__name__))
            return None
        # check customer number
        customer_account_no = self.get_customer_account_no(path)
        if customer_account_no != "12 3456 7890":
            self.logger.debug("{}: Invalid customer account number: {}".format(self.__class__.__name__, customer_account_no))
            return None
        data = self.get_date(path)
        if "month" not in data or "year" not in data:
            return None
        return pathlib.PurePath(
            "Telephone/Invoices/{year:04d}-{month:02d}.pdf".format(**data))