from typing import NamedTuple

class ExtrapolationParameters(NamedTuple):
    data_q_min: float
    point_1: float
    point_2: float
    point_3: float
    data_q_max: float