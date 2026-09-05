"use client"

import { useRef, useState } from "react"
import { FileCheck2, FlaskConical, LoaderCircle, RotateCcw, Upload } from "lucide-react"
import type { NoiseReport } from "@/lib/report"
import { ReportView } from "@/components/report-view"

function FileField({ id, label, hint, required }: { id: string; label: string; hint: string; required?: boolean }) {
  const [fileName, setFileName] = useState("")
  return (
    <label className="file-field" htmlFor={id}>
      <input id={id} name={id} type="file" accept=".csv,text/csv" required={required} onChange={(event) => setFileName(event.target.files?.[0]?.name ?? "")} />
      <span className="file-icon">{fileName ? <FileCheck2 aria-hidden="true" /> : <Upload aria-hidden="true" />}</span>
      <span><strong>{label}</strong><small>{fileName || hint}</small></span>
      <span className="file-action">Choisir</span>
    </label>
  )
}

export function AnalysisWorkspace() {
  const formRef = useRef<HTMLFormElement>(null)
  const [report, setReport] = useState<NoiseReport | null>(null)
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    setIsLoading(true)
    try {
      const response = await fetch("/api/analyze", { method: "POST", body: new FormData(event.currentTarget) })
      const data = await response.json()
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "L’analyse n’a pas pu être effectuée.")
      setReport(data as NoiseReport)
    } catch (caught) {
      setReport(null)
      setError(caught instanceof Error ? caught.message : "L’analyse n’a pas pu être effectuée.")
    } finally {
      setIsLoading(false)
    }
  }

  function reset() {
    formRef.current?.reset()
    setReport(null)
    setError("")
  }

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="NoiseDoseLab, accueil"><span className="brand-mark"><FlaskConical aria-hidden="true" /></span><span>NoiseDose<span>Lab</span></span></a>
        <p>Analyse déterministe de l’exposition sonore</p>
      </header>

      <div id="top" className="workspace">
        <aside className="control-panel" aria-labelledby="analysis-title">
          <div className="control-intro">
            <p className="eyebrow">Nouvelle analyse</p>
            <h1 id="analysis-title">Mesurer l’exposition, clairement.</h1>
            <p>Importez les relevés de terrain pour calculer l’exposition sonore de chaque travailleur.</p>
          </div>
          <form ref={formRef} onSubmit={submit} className="analysis-form">
            <fieldset>
              <legend>Fichiers de mesures</legend>
              <FileField id="baseline_csv" label="Mesures initiales" hint="Fichier CSV requis" required />
              <FileField id="scenario_csv" label="Scénarios" hint="Fichier CSV facultatif" />
            </fieldset>
            <fieldset>
              <legend>Paramètres d’analyse</legend>
              <div className="parameter-grid">
                <label htmlFor="reference_db"><span>Valeur de référence</span><span className="input-unit"><input id="reference_db" name="reference_db" type="number" step="any" min="0.000001" defaultValue="85" required /><small>dB</small></span></label>
                <label htmlFor="alert_margin_db"><span>Marge d’alerte</span><span className="input-unit"><input id="alert_margin_db" name="alert_margin_db" type="number" step="any" defaultValue="3" required /><small>dB</small></span></label>
              </div>
            </fieldset>
            {error && <div className="error-message" role="alert"><strong>Vérifiez vos données</strong><span>{error}</span></div>}
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={isLoading}>{isLoading ? <LoaderCircle className="spin" aria-hidden="true" /> : <FlaskConical aria-hidden="true" />}<span>{isLoading ? "Analyse en cours…" : "Lancer l’analyse"}</span></button>
              {(report || error) && <button className="reset-button" type="button" onClick={reset}><RotateCcw aria-hidden="true" />Réinitialiser</button>}
            </div>
          </form>
        </aside>

        <section className="results-area" aria-label="Résultats de l’analyse">
          {report ? <ReportView report={report} /> : (
            <div className="empty-state">
              <div className="waveform" aria-hidden="true">{[18, 34, 52, 28, 66, 44, 76, 38, 58, 24, 42, 18].map((height, index) => <i key={index} style={{ height }} />)}</div>
              <p className="eyebrow">En attente de mesures</p>
              <h2>Votre rapport apparaîtra ici</h2>
              <p>Sélectionnez un fichier de mesures initiales, puis lancez l’analyse.</p>
            </div>
          )}
        </section>
      </div>
    </main>
  )
}
