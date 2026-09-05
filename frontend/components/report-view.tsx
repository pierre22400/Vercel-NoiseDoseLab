import { Activity, ChevronDown } from "lucide-react"
import {
  formatNumber,
  reasonLabels,
  statusLabels,
  verdictLabels,
  type ExposureStatus,
  type NoiseReport,
} from "@/lib/report"

function StatusBadge({ status }: { status: ExposureStatus }) {
  return <span className={`status-badge status-${status}`}>{statusLabels[status]}</span>
}

function DataTable({ children, label }: { children: React.ReactNode; label: string }) {
  return (
    <div className="table-scroll" role="region" aria-label={label} tabIndex={0}>
      <table>{children}</table>
    </div>
  )
}

export function ReportView({ report }: { report: NoiseReport }) {
  return (
    <div className="report-stack" aria-live="polite">
      <section className={`verdict verdict-${report.verdict}`} aria-labelledby="verdict-title">
        <div>
          <p className="eyebrow">Verdict de l’analyse</p>
          <h2 id="verdict-title">{verdictLabels[report.verdict]}</h2>
        </div>
        <div className="verdict-reading">
          <span>{formatNumber(report.summary.max_worker_lex_8h)}</span>
          <small>dB LEX,8h max.</small>
        </div>
        {report.reasons.length > 0 && (
          <ul className="reason-list">
            {report.reasons.map((reason) => (
              <li key={reason}>{reasonLabels[reason] ?? reason}</li>
            ))}
          </ul>
        )}
      </section>

      <section className="metric-strip" aria-label="Résumé de l’analyse">
        <div><strong>{report.counts.valid_rows}</strong><span>lignes valides</span></div>
        <div><strong>{report.counts.workers}</strong><span>travailleurs</span></div>
        <div><strong>{report.counts.tasks}</strong><span>tâches</span></div>
        <div><strong>{report.summary.workers_above_reference}</strong><span>au-dessus de la référence</span></div>
      </section>

      <section className="report-panel" aria-labelledby="workers-title">
        <div className="section-heading">
          <div><p className="eyebrow">Exposition cumulée</p><h2 id="workers-title">Résultats par travailleur</h2></div>
          <span>{report.workers.length} résultat{report.workers.length > 1 ? "s" : ""}</span>
        </div>
        <DataTable label="Résultats par travailleur">
          <thead><tr><th>Travailleur</th><th>Tâches</th><th>Durée</th><th>LEX,8h</th><th>Ratio énergie</th><th>Statut</th></tr></thead>
          <tbody>
            {report.workers.map((worker) => (
              <tr key={worker.worker}>
                <td><strong>{worker.worker}</strong></td>
                <td>{worker.tasks.join(", ")}</td>
                <td>{formatNumber(worker.total_duration_h, 2)} h</td>
                <td className="mono">{formatNumber(worker.lex_8h)} dB</td>
                <td className="mono">{formatNumber(worker.energy_ratio, 3)}</td>
                <td><StatusBadge status={worker.status} /></td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </section>

      {report.scenarios.length > 0 && (
        <section className="report-panel" aria-labelledby="scenarios-title">
          <div className="section-heading"><div><p className="eyebrow">Projection</p><h2 id="scenarios-title">Scénarios comparés</h2></div></div>
          <div className="scenario-grid">
            {report.scenarios.map((scenario) => (
              <article className="scenario-card" key={scenario.scenario}>
                <h3>{scenario.scenario}</h3>
                <p><strong>{formatNumber(scenario.max_worker_lex_8h)}</strong> dB LEX,8h max.</p>
                <dl>
                  <div><dt>Écart au niveau initial</dt><dd>{formatNumber(scenario.reduction_db_vs_baseline_max)} dB</dd></div>
                  <div><dt>Travailleurs au-dessus</dt><dd>{scenario.workers_above_reference}</dd></div>
                  <div><dt>Segments au-dessus</dt><dd>{scenario.segments_above_reference}</dd></div>
                </dl>
              </article>
            ))}
          </div>
        </section>
      )}

      <details className="report-panel details-panel">
        <summary><span><Activity aria-hidden="true" /> Détail des segments</span><ChevronDown aria-hidden="true" /></summary>
        <DataTable label="Détail des segments">
          <thead><tr><th>Ligne</th><th>Travailleur</th><th>Tâche</th><th>Leq</th><th>Durée</th><th>Protection</th><th>LEX,8h</th><th>Statut</th></tr></thead>
          <tbody>
            {report.segments.map((segment) => (
              <tr key={segment.row_index}>
                <td>{segment.row_index}</td><td><strong>{segment.worker}</strong></td><td>{segment.task}</td>
                <td className="mono">{formatNumber(segment.leq_db)} dB</td><td>{formatNumber(segment.duration_h, 2)} h</td>
                <td>{formatNumber(segment.protection_db)} dB</td><td className="mono">{formatNumber(segment.segment_lex_8h)} dB</td>
                <td><StatusBadge status={segment.status} /></td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </details>

      <p className="report-footnote">Rapport {report.schema_version} · Référence {formatNumber(report.input.reference_db)} dB · Marge d’alerte {formatNumber(report.input.alert_margin_db)} dB</p>
    </div>
  )
}
