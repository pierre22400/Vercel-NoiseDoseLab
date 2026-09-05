export type ExposureStatus = "below_alert" | "alert" | "above_reference"
export type Verdict = "pass" | "warn" | "fail"

export interface Segment {
  row_index: number
  worker: string
  task: string
  leq_db: number
  duration_h: number
  protection_db: number
  effective_db: number
  sound_energy: number
  normalized_8h_energy: number
  segment_lex_8h: number | null
  energy_ratio: number
  status: ExposureStatus
}

export interface WorkerResult {
  worker: string
  segments: number
  tasks: string[]
  total_duration_h: number
  total_sound_energy: number
  normalized_8h_energy: number
  lex_8h: number | null
  energy_ratio: number
  status: ExposureStatus
}

export interface ScenarioResult {
  scenario: string
  max_worker_lex_8h: number | null
  max_worker_energy_ratio: number
  workers_above_reference: number
  segments_above_reference: number
  reduction_db_vs_baseline_max: number | null
}

export interface NoiseReport {
  schema_version: string
  status: "ok"
  input: {
    csv: string
    scenario_csv: string | null
    reference_db: number
    alert_margin_db: number
  }
  counts: {
    total_rows: number
    valid_rows: number
    invalid_rows: number
    workers: number
    tasks: number
    scenarios: number
  }
  segments: Segment[]
  workers: WorkerResult[]
  summary: {
    reference_db: number
    max_worker_lex_8h: number | null
    max_worker_energy_ratio: number
    workers_above_reference: number
    segments_above_reference: number
  }
  scenarios: ScenarioResult[]
  verdict: Verdict
  reasons: string[]
}

export const statusLabels: Record<ExposureStatus, string> = {
  below_alert: "Sous le seuil d’alerte",
  alert: "Zone d’alerte",
  above_reference: "Au-dessus de la référence",
}

export const verdictLabels: Record<Verdict, string> = {
  pass: "Conforme",
  warn: "À surveiller",
  fail: "Non conforme",
}

export const reasonLabels: Record<string, string> = {
  no_valid_rows: "Aucune ligne exploitable n’a été trouvée.",
  invalid_rows_ignored: "Certaines lignes invalides ont été ignorées.",
  worker_duration_over_24h: "La durée cumulée d’au moins un travailleur dépasse 24 h.",
  noise_above_reference: "Au moins une exposition dépasse la valeur de référence.",
  noise_at_or_above_alert: "Au moins une exposition atteint la zone d’alerte.",
  all_screening_checks_passed: "Tous les contrôles de dépistage sont conformes.",
}

export function formatNumber(value: number | null, digits = 1): string {
  if (value === null) return "—"
  return new Intl.NumberFormat("fr-FR", { maximumFractionDigits: digits }).format(value)
}
