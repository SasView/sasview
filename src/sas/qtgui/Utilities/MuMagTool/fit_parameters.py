from dataclasses import dataclass

@dataclass
class FitParameters:
    q_max: float
    min_applied_field: float
    exchange_A_min: float
    exchange_A_max: float
    exchange_A_n: int
    experiment_geometry: str