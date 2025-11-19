"""
Utility functions for slicers
"""

def generate_unique_plot_id(base_id, item):
    """
    Generate a unique plot ID by checking existing plots in the data tree.

    :param base_id: The base identifier string (e.g., "SectorQ" + data.name)
    :param item: The current item in the data explorer tree
    :return: A unique ID string, either base_id or base_id_N where N is a number
    """
    parent_item = item if item.parent() is None else item.parent()

    existing = 0
    for i in range(parent_item.rowCount()):
        it = parent_item.child(i)
        d = it.data()
        if hasattr(d, "id") and isinstance(d.id, str) and d.id.startswith(base_id):
            existing += 1
        for j in range(it.rowCount()):
            it2 = it.child(j)
            d2 = it2.data()
            if hasattr(d2, "id") and isinstance(d2.id, str) and d2.id.startswith(base_id):
                existing += 1

    return base_id if existing == 0 else f"{base_id}_{existing + 1}"
