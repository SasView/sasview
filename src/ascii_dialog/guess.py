#!/usr/bin/env python3

def guess_seperator(raw_csv: list[str]) -> str | None:
    """Try to guess what the seperator is in raw_csv, and return it. Will return
    None if a seperator cannot be guessed, and thus will likely require manual
    intervention from the user."""

    candidates = [",", ";", ":", "\t"]

    for sep in candidates:
        if all([sep in line for line in raw_csv]):
            return sep

    # If none of the candidate appear to be the seperator, then the seperator is
    # potentially a number of whitespaces (n).
    #
    # Try to determine what n is.

    # Maximum whitespace seperation is 15 to stop this from going into an
    # infinite loop. This might not be needed later.
    for candidate_n in range(1, 15):
        candidate_sep = " " * candidate_n
        attempted_split = raw_csv[0].split(candidate_sep)
        if '' not in attempted_split:
            return candidate_sep

    # No seperator found.
    return None
