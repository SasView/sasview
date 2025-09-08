from typing import Any


def unique_preserve_order(seq: list[Any]) -> list[Any]:
    """ Remove duplicates from list preserving order
    Fastest according to benchmarks at https://www.peterbe.com/plog/uniqifiers-benchmark
    """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]
