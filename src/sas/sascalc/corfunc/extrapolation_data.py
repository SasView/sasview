from typing import NamedTuple, Optional


class ExtrapolationParameters(NamedTuple):
    """ Represents the parameters defining extrapolation"""
    data_q_min: float
    point_1: float
    point_2: float
    point_3: float
    data_q_max: float


class ExtrapolationInteractionState(NamedTuple):
    """ Represents the state of the slider used to control extrapolation parameters

    Contains extrapolation parameters along with the representation of the hover state.
    """
    extrapolation_parameters: ExtrapolationParameters
    working_line_id: Optional[int] = None
    dragging_line_position: Optional[float] = None