#!/usr/bin/env python3

from dataset_types import DatasetType

def guess_column_count(split_csv: list[list[str]], starting_pos: int) -> int:
    """Guess the amount of columns present in the data."""
    return len(split_csv[starting_pos])

def guess_columns(col_count: int, dataset_type: DatasetType) -> list[str]:
    """Based on the amount of columns specified in col_count, try to find a set
    of columns that best matchs the dataset_type.

    """
    # Ideally we want an exact match but if the ordering is bigger than the col
    # count then we can accept that as well.
    for order_list in dataset_type.expected_orders:
        if len(order_list) >= col_count:
            return order_list

    return dataset_type.expected_orders[-1]

def guess_starting_position(split_csv: list[list[str]]) -> int:
    """Try to look for a line where the first item in the row can be converted
    to a number. If such a line doesn't exist, try to look for a line where the
    first item in the row can be converted to a number. If such a line doesn't
    exist, then just return 0 as the starting position.

    """
    for i, row in enumerate(split_csv):
        if row[0].replace('.', '').replace('-', '').isdigit():
            return i
    return 0
