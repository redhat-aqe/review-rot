"""Simple helper functions"""
import re

WIP_REGEX_PATTERN = r"^(\[(WIP|Draft)\]|(WIP|Draft))(:|\s)?"


def is_wip(title):
    match = re.match(WIP_REGEX_PATTERN, title, re.IGNORECASE)
    return bool(match)
