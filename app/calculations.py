import math

from app.models import BaselineRow


def reference_energy(reference_db: float) -> float:
    return 10.0 ** (reference_db / 10.0)


def logarithmic_level(normalized_energy: float) -> float | None:
    if normalized_energy <= 0.0:
        return None
    return 10.0 * math.log10(normalized_energy)


def classify_level(
    lex_8h: float | None, reference_db: float, alert_margin_db: float
) -> str:
    if lex_8h is None or lex_8h < reference_db - alert_margin_db:
        return "below_alert"
    if lex_8h <= reference_db:
        return "alert"
    return "above_reference"


def calculate_segment(
    row: BaselineRow, reference_db: float, alert_margin_db: float
) -> dict[str, object]:
    effective_db = row.leq_db - row.protection_db
    sound_energy = row.duration_h * (10.0 ** (effective_db / 10.0))
    normalized_8h_energy = sound_energy / 8.0
    segment_lex_8h = logarithmic_level(normalized_8h_energy)
    energy_ratio = normalized_8h_energy / reference_energy(reference_db)
    return {
        "row_index": row.row_index,
        "worker": row.worker,
        "task": row.task,
        "leq_db": row.leq_db,
        "duration_h": row.duration_h,
        "protection_db": row.protection_db,
        "effective_db": effective_db,
        "sound_energy": sound_energy,
        "normalized_8h_energy": normalized_8h_energy,
        "segment_lex_8h": segment_lex_8h,
        "energy_ratio": energy_ratio,
        "status": classify_level(segment_lex_8h, reference_db, alert_margin_db),
    }
