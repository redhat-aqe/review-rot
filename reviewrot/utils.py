"""Simple helper functions."""
import re

WIP_REGEX_PATTERN = r"^(\[(WIP|Draft)\]|(WIP|Draft))(:|\s)?"


def is_wip(title):
    """
    Returns True only if title indicates work-in-progress.

    Args:
        title (str): Review/pull-request/merge-request title

    Returns:
        True only if the title indicates work-in-progress,
        False otherwise
    """
    match = re.match(WIP_REGEX_PATTERN, title, re.IGNORECASE)
    return bool(match)
