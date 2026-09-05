import json


def render_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False)


def _value(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def render_text(payload: dict[str, object]) -> str:
    input_data = payload["input"]
    counts = payload["counts"]
    summary = payload["summary"]
    assert isinstance(input_data, dict)
    assert isinstance(counts, dict)
    assert isinstance(summary, dict)

    lines = [
        "NoiseDoseLab",
        f"status: {_value(payload['status'])}",
        "input:",
    ]
    lines.extend(f"  {key}: {_value(value)}" for key, value in input_data.items())
    lines.append("counts:")
    lines.extend(f"  {key}: {_value(value)}" for key, value in counts.items())
    lines.append("segments:")
    for segment in payload["segments"]:
        assert isinstance(segment, dict)
        lines.append("  segment:")
        lines.extend(f"    {key}: {_value(value)}" for key, value in segment.items())
    lines.append("workers:")
    for worker in payload["workers"]:
        assert isinstance(worker, dict)
        lines.append("  worker:")
        lines.extend(f"    {key}: {_value(value)}" for key, value in worker.items())
    lines.append("summary:")
    lines.extend(f"  {key}: {_value(value)}" for key, value in summary.items())
    lines.append("scenarios:")
    for scenario in payload["scenarios"]:
        assert isinstance(scenario, dict)
        lines.append("  scenario:")
        lines.extend(f"    {key}: {_value(value)}" for key, value in scenario.items())
    lines.extend(
        [
            f"verdict: {_value(payload['verdict'])}",
            f"reasons: {_value(payload['reasons'])}",
        ]
    )
    return "\n".join(lines)
