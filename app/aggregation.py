from collections import defaultdict

from app.calculations import classify_level, logarithmic_level, reference_energy


def aggregate_workers(
    segments: list[dict[str, object]], reference_db: float, alert_margin_db: float
) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for segment in segments:
        grouped[str(segment["worker"])].append(segment)

    workers: list[dict[str, object]] = []
    for worker_name in sorted(grouped):
        worker_segments = grouped[worker_name]
        total_duration_h = sum(float(item["duration_h"]) for item in worker_segments)
        total_sound_energy = sum(float(item["sound_energy"]) for item in worker_segments)
        normalized_8h_energy = total_sound_energy / 8.0
        lex_8h = logarithmic_level(normalized_8h_energy)
        workers.append(
            {
                "worker": worker_name,
                "segments": len(worker_segments),
                "tasks": sorted({str(item["task"]) for item in worker_segments}),
                "total_duration_h": total_duration_h,
                "total_sound_energy": total_sound_energy,
                "normalized_8h_energy": normalized_8h_energy,
                "lex_8h": lex_8h,
                "energy_ratio": normalized_8h_energy / reference_energy(reference_db),
                "status": classify_level(lex_8h, reference_db, alert_margin_db),
            }
        )
    return workers


def build_summary(
    segments: list[dict[str, object]],
    workers: list[dict[str, object]],
    reference_db: float,
) -> dict[str, object]:
    levels = [float(worker["lex_8h"]) for worker in workers if worker["lex_8h"] is not None]
    ratios = [float(worker["energy_ratio"]) for worker in workers]
    return {
        "reference_db": reference_db,
        "max_worker_lex_8h": max(levels) if levels else None,
        "max_worker_energy_ratio": max(ratios) if ratios else 0.0,
        "workers_above_reference": sum(
            worker["status"] == "above_reference" for worker in workers
        ),
        "segments_above_reference": sum(
            segment["status"] == "above_reference" for segment in segments
        ),
    }
