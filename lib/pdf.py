import errno
import os
import pathlib
import subprocess
import tempfile

from typing import List, Union

class PDF:
    """
    The PDF class represents a PDF file. It provides functions and attributes to retrieve data about the file (e.g. the
    number of pages) and to extract text (e.g. via OCR) from it.
    """
    def __init__(self, path: Union[pathlib.Path, str]):
        """
        Creates a PDF object for the given PDF file.
        :param path: The path to a PDF file. The file must exist at the time of calling the constructor.
        """
        if isinstance(path, str):
            path = pathlib.Path(path)
        self.path: pathlib.Path = path.resolve()
        """The path to the PDF file."""
        if not self.path.is_file():
            raise FileNotFoundError(errno.ENOENT, "PDF does not exist or is not a file", str(self.path))
        # Determine how many pages the PDF has
        self.pages: int = 0
        """The number of pages in the PDF."""
        for line in subprocess.run(["pdfinfo", path], check=True, stdout=subprocess.PIPE, universal_newlines=True).stdout.splitlines():
            line = line.rpartition(":")
            if line[0] != "Pages":
                continue
            self.pages = int(line[2].strip())

    def ocr(self, page: int, x: int, y: int, width: int, height: int, strip: bool = True, lang: str = "deu") -> str:
        """
        Run OCR on the PDF constrained to the given coordinates and return the recognized string.
        Note: Coordinates are pixels in a 72 ppi rasterization of the PDF.
        :param page: Which page to run OCR on, starting from 1 (!)
        :param x: The X coordinate of the upper left corner, counted from the left border of the page.
        :param y: The Y coordinate of the upper left corner, counted from the top of the page.
        :param width: The width of the area to run OCR on.
        :param height: The height of the area to run OCR on.
        :param strip: Whether to strip spaces from the left and right of the result.
        :param lang: The language to use for OCR heuristics, default to German ("deu").
        :return: The recognized string.
        """
        # Translate coordinates for 150 ppi
        x = round(x * 150 / 72)
        y = round(y * 150 / 72)
        width = round(width * 150 / 72)
        height = round(height * 150 / 72)
        # Raster the area
        handle, image_file = tempfile.mkstemp(suffix=".png")
        os.close(handle)
        subprocess.run(
            ["pdftocairo", "-png", "-singlefile", "-r", "150", "-f", str(page), "-l", str(page), "-x", str(x),
             "-y", str(y), "-W", str(width), "-H", str(height), str(self.path), image_file[:-4]],
            check=True,
        )
        # Run OCR and retrieve the text
        string: str = subprocess.run(
            ["tesseract", image_file, "-", "-l", lang],
            check=True, stdout=subprocess.PIPE, universal_newlines=True
        ).stdout
        # Remove the temporary file
        pathlib.Path(image_file).unlink()
        return string.strip() if strip else string

    def get_text(self, page: int, x: int, y: int, width: int, height: int, strip: bool = True) -> str:
        """
        Extract embedded text from PDF at given coordinates, return as string.
        Note: This function does NOT run OCR. It only extracts text which is already embedded in the PDF.
        Note: Coordinates are pixels in a 72 ppi rasterization of the PDF.
        :param page: Which page to select text from, starting from 1 (!)
        :param x: The X coordinate of the upper left corner, counted from the left border of the page.
        :param y: The Y coordinate of the upper left corner, counted from the top of the page.
        :param width: The width of the area to extract text from.
        :param height: The height of the area to extract text from.
        :param strip: Whether to strip spaces from the left and right of the result.
        :return: The extracted string.
        """
        string: str = subprocess.run(
        [
                "pdftotext",
                 "-f", str(page),
                 "-l", str(page),
                 "-x", str(x),
                 "-y", str(y),
                 "-W", str(width),
                 "-H", str(height),
                 str(self.path), "-"
            ],
            check=True, stdout=subprocess.PIPE, universal_newlines=True
        ).stdout
        return string.strip() if strip else string