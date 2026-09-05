def evaluate_quality(
    valid_rows: int,
    invalid_rows: int,
    workers: list[dict[str, object]],
    reference_db: float,
    alert_margin_db: float,
) -> tuple[str, list[str]]:
    no_valid_rows = valid_rows == 0
    duration_over_24h = any(
        float(worker["total_duration_h"]) > 24.0 for worker in workers
    )
    above_reference = any(
        worker["lex_8h"] is not None
        and float(worker["lex_8h"]) > reference_db
        for worker in workers
    )

    if no_valid_rows or duration_over_24h or above_reference:
        reasons = []
        if no_valid_rows:
            reasons.append("no_valid_rows")
        if duration_over_24h:
            reasons.append("worker_duration_over_24h")
        if above_reference:
            reasons.append("noise_above_reference")
        return "fail", reasons

    at_or_above_alert = any(
        worker["lex_8h"] is not None
        and float(worker["lex_8h"]) >= reference_db - alert_margin_db
        for worker in workers
    )
    if invalid_rows > 0 or at_or_above_alert:
        reasons = []
        if invalid_rows > 0:
            reasons.append("invalid_rows_ignored")
        if at_or_above_alert:
            reasons.append("noise_at_or_above_alert")
        return "warn", reasons

    return "pass", ["all_screening_checks_passed"]
