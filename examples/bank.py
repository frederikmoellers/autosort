import json
import lib.pdf
import logging
import pathlib
import re

from typing import Dict, List, Optional
from sorters import Sorter


# human-readable names of bank accounts
ACCOUNT_NAMES = {
    "1234567890": "Cheque Account ",
    "1234567891": "Savings Account",
}


class AccountStatement(Sorter):
    def __init__(self, logger: logging.Logger):
        Sorter.__init__(self, logger)
        self.re = re.compile(r'(?P<acc_number>\d{10})_\d{4}_Nr\.0(?P<issue>\d{2})_Statement_from_(?P<year>\d{4})\.(?P<month>\d{2})\.(?P<day>\d{2})_\d{14}\.pdf')
        self.foldernames = {
            "1234567890": "Cheque Account - 12345678990",
            "1234567891": "Savings Account - 1234567891",
        }

    @staticmethod
    def extract_date(pdf: lib.pdf.PDF) -> Dict[str, str]:
        # Account number
        account_number: str = pdf.get_text(1, 434, 177, 61, 12).replace(" ", "")
        data: Dict[str, str] = {
            "acc_number": account_number,
        }
        # Issue
        data["issue"], data["year"] = pdf.get_text(1, 528, 140, 53, 13).split("/")
        data["issue"] = data["issue"].rjust(2, "0")
        return data

    def sort(self, path: pathlib.Path) -> Optional[pathlib.PurePath]:
        data: Dict[str, str]
        match = self.re.match(path.name)
        if not match:
            return None
        data = {
            "acc_number": match.group("acc_number"),
            "issue": match.group("issue"),
            "year": match.group("year"),
        }
        pdf: lib.pdf.PDF = lib.pdf.PDF(path)
        data.update(self.extract_data(pdf))
        data["foldername"] = self.foldernames[data["acc_number"]]
        return pathlib.PurePath(
            "Bank/Statements/{data[foldername]}/{data[year]}-{data[issue]}.pdf".format(data=data))


class CreditCardStatement(Sorter):
    def __init__(self, logger: logging.Logger):
        Sorter.__init__(self, logger)
        self.re = re.compile(r'XXXXXXXXXXXXX(?P<cc_number>\d{3})_\d{4}_Credit_Card_Statement_from_(?P<year>\d{4})\.(?P<month>\d{2})\.(?P<day>\d{2})_\d{14}\.pdf')
        # only the last 3 digits are included in the filename, so we only use those for matching
        self.foldernames = {
            "123": "Credit Card A",
            "456": "Credit Card B",
        }

    @staticmethod
    def extract_date(pdf: lib.pdf.PDF) -> Dict[str, str]:
        pdf_date: str = pdf.get_text(1, 153, 270, 75, 15)
        return {
            "day": pdf_date[0:2],
            "month": pdf_date[3:5],
            "year": pdf_date[6:10]
        }

    def sort(self, path: pathlib.Path) -> Optional[pathlib.PurePath]:
        data: Dict[str, str]
        match = self.re.match(path.name)
        if not match:
            self.logger.debug("{}: No match.".format(self.__class__.__name__))
            return None
        data = {
            "day": match.group("day"),
            "month": match.group("month"),
            "year": match.group("year"),
            "cc_number": match.group("cc_number"),
        }
        pdf: lib.pdf.PDF = lib.pdf.PDF(path)
        data.update(self.extract_date(pdf))
        data["foldername"] = self.foldernames[data["cc_number"]]
        return pathlib.PurePath(
            "Bank/Statements/{data[foldername]}/{data[year]}-{data[month]}-{data[day]}.pdf".format(data=data))


class Message(Sorter):
    def __init__(self, logger: logging.Logger):
        Sorter.__init__(self, logger)
        self.re = re.compile(r'(?P<account_nr>\d{10})_\d{4}_(?P<title>Message)_from_(?P<year>\d{4})\.(?P<month>\d{2})\.(?P<day>\d{2})_\d+\.pdf')

    @staticmethod
    def extract_date(pdf: lib.pdf.PDF) -> Dict[str, str]:
        pdf_date: str = pdf.get_text(1, 390, 154, 52, 10)
        return {
            "day": pdf_date[0:2],
            "month": pdf_date[3:5],
            "year": pdf_date[6:10]
        }

    @staticmethod
    def extract_title(pdf: lib.pdf.PDF) -> str:
        return pdf.get_text(1, 108, 317, 474, 17)

    def sort(self, path: pathlib.Path) -> Optional[pathlib.PurePath]:
        data: Dict[str, str]
        match = self.re.match(path.name)
        if not match:
            self.logger.debug("{}: No match.".format(self.__class__.__name__))
            return None
        data = {
            "day": match.group("day"),
            "month": match.group("month"),
            "year": match.group("year"),
            "account_nr": match.group("account_nr"),
        }
        pdf: lib.pdf.PDF = lib.pdf.PDF(path)
        data.update(self.extract_date(pdf))
        data["title"] = self.extract_title(pdf)
        self.logger.debug("{}: Match! Extracted data:".format(self.__class__.__name__))
        self.logger.debug(json.dumps(data))
        if data["title"] == "Interest rate adjustment":
            data["account"] = ACCOUNT_NAMES[data["account_nr"]]
            return pathlib.PurePath(
                "Bank/Interest Rate Adjustments/{data[year]}-{data[month]}-{data[day]} - {data[title]} {data[account]}.pdf".format(data=data))
        return None

