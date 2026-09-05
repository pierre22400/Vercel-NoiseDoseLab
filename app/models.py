from dataclasses import dataclass


@dataclass(frozen=True)
class BaselineRow:
    row_index: int
    worker: str
    task: str
    leq_db: float
    duration_h: float
    protection_db: float


@dataclass(frozen=True)
class ScenarioDefinition:
    scenario: str
    leq_delta_db: float
    duration_factor: float
    protection_delta_db: float
