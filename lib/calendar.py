from typing import Dict, List, Optional

month_names: Dict[str, List[str]] = {
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
}


def month_to_number_str(month: str, language: Optional[str] = None) -> str:
    """
    Returns the number of the month (as a string) given its name. Optionally, the language can be specified by its ISO
    code ("de", "en" etc.). If no language is specified, all languages will be tested in alphabetical order. The first
    match is returned.
    :param month: The name of the month.
    :param language: The language code (optional).
    :return: The number of the month as a 2-digit string, zero-padded
    """
    index: int = -1
    if not language:
        languages = month_names.keys()
    else:
        languages = [language]
    for language in languages:
        try:
            index = month_names[language].index(month)
            break
        except:
            pass
    if index == -1:
        raise ValueError("Month '{}' not found in language '{}'".format(month, language))
    return "{:02d}".format(index + 1)