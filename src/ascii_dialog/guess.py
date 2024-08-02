#!/usr/bin/env python3

from dataset_types import DatasetType


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

def guess_column_count(split_csv: list[list[str]], starting_pos: int) -> int:
    """Guess the amount of columns present in the data."""
    return len(split_csv[starting_pos])

def guess_columns(col_count: int, dataset_type: DatasetType) -> list[str]:
    # Ideally we want an exact match but if the ordering is bigger than the col
    # count then we can accept that as well.
    for order_list in dataset_type.expected_orders:
        if len(order_list) >= col_count:
            return order_list

    return dataset_type.expected_orders[-1]

def guess_starting_position(split_csv: list[list[str]]) -> int:
    """Try to look for a line where the first item in the row can be converted
    to a number. If such a line doesn't existTry to look for a line where the
    first item in the row can be converted to a number. If such a line doesn't
    exist, then just return 0 as the starting position."""
    for i, row in enumerate(split_csv):
        if row[0].replace('.', '').replace('-', '').isdigit():
            return i
    return 0