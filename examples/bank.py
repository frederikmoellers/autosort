import json
import logging
import pathlib
import re
import subprocess

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
    def extract_data(path: pathlib.Path) -> Dict[str, str]:
        # Account number
        account_number: str = subprocess.check_output(
            ["pdftotext", "-f", "1", "-l", "1", "-x", "434", "-y", "177", "-W", "61", "-H", "12",
             str(path.resolve()), "-"]
        ).decode().strip().replace(" ", "")
        data: Dict[str, str] = {
            "acc_number": account_number,
        }
        # Issue
        issue_year: List[str] = subprocess.check_output(
            ["pdftotext", "-f", "1", "-l", "1", "-x", "528", "-y", "140", "-W", "53", "-H", "13",
             str(path.resolve()), "-"]
        ).decode().strip().split("/")
        data["issue"] = issue_year[0].rjust(2, "0")
        data["year"] = issue_year[1]
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
        data.update(self.extract_data(path))
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
    def extract_date(path: pathlib.Path) -> Dict[str, str]:
        pdf_date: str = subprocess.check_output(
            ["pdftotext", "-f", "1", "-l", "1", "-x", "153", "-y", "270", "-W", "75", "-H", "15", str(path.resolve()),
             "-"]
        ).decode().strip()
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
        data.update(self.extract_date(path))
        data["foldername"] = self.foldernames[data["cc_number"]]
        return pathlib.PurePath(
            "Bank/Statements/{data[foldername]}/{data[year]}-{data[month]}-{data[day]}.pdf".format(data=data))


class Message(Sorter):
    def __init__(self, logger: logging.Logger):
        Sorter.__init__(self, logger)
        self.re = re.compile(r'(?P<account_nr>\d{10})_\d{4}_(?P<title>Message)_from_(?P<year>\d{4})\.(?P<month>\d{2})\.(?P<day>\d{2})_\d+\.pdf')

    @staticmethod
    def extract_date(path: pathlib.Path) -> Dict[str, str]:
        pdf_date: str = subprocess.check_output(
            ["pdftotext", "-f", "1", "-l", "1", "-x", "390", "-y", "154", "-W", "52", "-H", "10", str(path.resolve()),
             "-"]
        ).decode().strip()
        return {
            "day": pdf_date[0:2],
            "month": pdf_date[3:5],
            "year": pdf_date[6:10]
        }

    @staticmethod
    def extract_title(path: pathlib.Path) -> str:
        return subprocess.check_output(
            ["pdftotext", "-f", "1", "-l", "1", "-x", "108", "-y", "317", "-W", "474", "-H", "17", str(path.resolve()),
             "-"]
        ).decode().strip()

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
        data.update(self.extract_date(path))
        data["title"] = self.extract_title(path)
        self.logger.debug("{}: Match! Extracted data:".format(self.__class__.__name__))
        self.logger.debug(json.dumps(data))
        if data["title"] == "Interest rate adjustment":
            data["account"] = ACCOUNT_NAMES[data["account_nr"]]
            return pathlib.PurePath(
                "Bank/Interest Rate Adjustments/{data[year]}-{data[month]}-{data[day]} - {data[title]} {data[account]}.pdf".format(data=data))
        return None

