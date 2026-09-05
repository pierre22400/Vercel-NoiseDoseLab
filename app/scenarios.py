from app.aggregation import aggregate_workers, build_summary
from app.calculations import calculate_segment
from app.models import BaselineRow, ScenarioDefinition


def analyze_scenarios(
    baseline_rows: list[BaselineRow],
    definitions: list[ScenarioDefinition],
    reference_db: float,
    alert_margin_db: float,
    baseline_max_lex_8h: float | None,
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for definition in definitions:
        scenario_rows = [
            BaselineRow(
                row_index=row.row_index,
                worker=row.worker,
                task=row.task,
                leq_db=row.leq_db + definition.leq_delta_db,
                duration_h=row.duration_h * definition.duration_factor,
                protection_db=row.protection_db + definition.protection_delta_db,
            )
            for row in baseline_rows
        ]
        segments = [
            calculate_segment(row, reference_db, alert_margin_db)
            for row in scenario_rows
        ]
        workers = aggregate_workers(segments, reference_db, alert_margin_db)
        summary = build_summary(segments, workers, reference_db)
        scenario_max = summary["max_worker_lex_8h"]
        reduction = None
        if baseline_max_lex_8h is not None and scenario_max is not None:
            reduction = baseline_max_lex_8h - float(scenario_max)
        results.append(
            {
                "scenario": definition.scenario,
                "max_worker_lex_8h": scenario_max,
                "max_worker_energy_ratio": summary["max_worker_energy_ratio"],
                "workers_above_reference": summary["workers_above_reference"],
                "segments_above_reference": summary["segments_above_reference"],
                "reduction_db_vs_baseline_max": reduction,
            }
        )
    return results
