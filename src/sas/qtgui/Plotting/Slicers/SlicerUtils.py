"""
Utility functions for slicers
"""

def _count_matching_ids(item, base_id: str) -> int:
    """
    Recursively count items with IDs starting with base_id.
    
    :param item: Tree item to search
    :param base_id: The base identifier to match
    :return: Count of matching items in this subtree
    """
    count = 0

    # Check current item
    d = item.data()
    if hasattr(d, "id") and isinstance(d.id, str) and d.id.startswith(base_id):
        count += 1

    # Recursively check all children
    for i in range(item.rowCount()):
        count += _count_matching_ids(item.child(i), base_id)

    return count


def generate_unique_plot_id(base_id: str, item) -> str:
    """
    Generate a unique plot ID by checking existing plots in the data tree.

    :param base_id: The base identifier string (e.g., "SectorQ" + data.name)
    :param item: The current item in the data explorer tree
    :return: A unique ID string, either base_id or base_id_N where N is a number
    """
    parent_item = item if item.parent() is None else item.parent()
    existing = _count_matching_ids(parent_item, base_id)

    return base_id if existing == 0 else f"{base_id}_{existing + 1}"
