import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, describe, expect, it, vi } from "vitest"
import { AnalysisWorkspace } from "@/components/analysis-workspace"
import type { NoiseReport } from "@/lib/report"

const report: NoiseReport = {
  schema_version: "noisedoselab_level1_report.v1",
  status: "ok",
  input: { csv: "mesures.csv", scenario_csv: null, reference_db: 85, alert_margin_db: 3 },
  counts: { total_rows: 1, valid_rows: 1, invalid_rows: 0, workers: 1, tasks: 1, scenarios: 0 },
  segments: [{ row_index: 1, worker: "alice", task: "press", leq_db: 80, duration_h: 8, protection_db: 0, effective_db: 80, sound_energy: 800000000, normalized_8h_energy: 100000000, segment_lex_8h: 80, energy_ratio: 0.316228, status: "below_alert" }],
  workers: [{ worker: "alice", segments: 1, tasks: ["press"], total_duration_h: 8, total_sound_energy: 800000000, normalized_8h_energy: 100000000, lex_8h: 80, energy_ratio: 0.316228, status: "below_alert" }],
  summary: { reference_db: 85, max_worker_lex_8h: 80, max_worker_energy_ratio: 0.316228, workers_above_reference: 0, segments_above_reference: 0 },
  scenarios: [], verdict: "pass", reasons: [],
}

afterEach(() => vi.restoreAllMocks())

describe("AnalysisWorkspace", () => {
  it("shows the expected analysis fields", () => {
    render(<AnalysisWorkspace />)
    expect(screen.getByLabelText(/Mesures initiales/)).toBeRequired()
    expect(screen.getByLabelText(/Scénarios/)).not.toBeRequired()
    expect(screen.getByLabelText(/Valeur de référence/)).toHaveValue(85)
    expect(screen.getByRole("button", { name: "Lancer l’analyse" })).toBeEnabled()
  })

  it("submits the form and renders the real report shape", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify(report), { status: 200, headers: { "Content-Type": "application/json" } }))
    const user = userEvent.setup()
    render(<AnalysisWorkspace />)
    await user.upload(screen.getByLabelText(/Mesures initiales/), new File(["csv"], "mesures.csv", { type: "text/csv" }))
    fireEvent.submit(screen.getByRole("button", { name: "Lancer l’analyse" }).closest("form")!)
    expect(await screen.findByRole("heading", { name: "Conforme" })).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Résultats par travailleur" })).toBeInTheDocument()
    expect(screen.getAllByText("alice").length).toBeGreaterThan(0)
    expect(globalThis.fetch).toHaveBeenCalledWith("/api/analyze", expect.objectContaining({ method: "POST", body: expect.any(FormData) }))
  })

  it("shows a clear API validation error", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ detail: "missing required column: duration_h" }), { status: 422, headers: { "Content-Type": "application/json" } }))
    const user = userEvent.setup()
    render(<AnalysisWorkspace />)
    await user.upload(screen.getByLabelText(/Mesures initiales/), new File(["bad"], "bad.csv", { type: "text/csv" }))
    fireEvent.submit(screen.getByRole("button", { name: "Lancer l’analyse" }).closest("form")!)
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("missing required column: duration_h"))
    expect(screen.queryByRole("heading", { name: "Résultats par travailleur" })).not.toBeInTheDocument()
  })
})
