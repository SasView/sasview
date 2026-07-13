from dataclasses import dataclass
from typing import Any, NamedTuple


def unique_preserve_order(seq: list[Any]) -> list[Any]:
    """ Remove duplicates from list preserving order
    Fastest according to benchmarks at https://www.peterbe.com/plog/uniqifiers-benchmark
    """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


@dataclass
class SettableExtrapolationParameters:
    """ Extrapolation parameters that can be set by the user"""
    point_1: float
    point_2: float
    point_3: float


class ExtrapolationParameters(NamedTuple):
    """ Represents the parameters defining extrapolation"""
    ex_q_min: float | None
    data_q_min: float
    point_1: float
    point_2: float
    point_3: float
    data_q_max: float
    ex_q_max: float | None


@dataclass
class ExtrapolationInteractionState:
    """ Represents the state of the slider used to control extrapolation parameters

    Contains extrapolation parameters along with the representation of the hover state.
    """
    extrapolation_parameters: ExtrapolationParameters
    working_line_id: int | None = None
    dragging_line_position: float | None = None
