from typing import NamedTuple, Optional

class ExtrapolationParameters(NamedTuple):
    data_q_min: float
    point_1: float
    point_2: float
    point_3: float
    data_q_max: float


class ExtrapolationInteractionState(NamedTuple):
    extrapolation_parameters: ExtrapolationParameters
    working_line_id: Optional[int]
    dragging_line_position: Optional[float]