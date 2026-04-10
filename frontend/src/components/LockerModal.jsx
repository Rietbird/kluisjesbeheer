import { useState, useEffect } from 'react'
import { api } from '../api'
import AssignForm from './AssignForm'
import EndRentalForm from './EndRentalForm'
import { useInstellingen } from '../context/InstellingenContext'
import { formatDate } from '../utils/formatDate'

function InfoRow({ label, children }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-600 last:border-0">
      <span className="text-slate-500 dark:text-slate-400">{label}</span>
      <span className="font-medium text-right text-slate-800 dark:text-slate-200">{children}</span>
    </div>
  )
}

function StatusBadge({ status, sleutelNietIngeleverd }) {
  const cls = status === 'uitgeleend' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300'
    : status === 'defect' ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300'
    : sleutelNietIngeleverd ? 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300'
    : 'bg-sky-100 text-sky-800 dark:bg-sky-900/50 dark:text-sky-300'
  return <span className={`px-3 py-1 rounded-full font-semibold ${cls}`}>{status}</span>
}

export default function LockerModal({ kluisje, onClose, onUpdate }) {
  const [detail, setDetail] = useState(kluisje)
  const [geschiedenis, setGeschiedenis] = useState([])
  const [opmerkingen, setOpmerkingen] = useState(kluisje.opmerkingen || '')
  const [mode, setMode] = useState(null)
  const [savingStatus, setSavingStatus] = useState(null)
  const { borgActiefVoor } = useInstellingen()

  useEffect(() => {
    setDetail(kluisje)
    setOpmerkingen(kluisje.opmerkingen || '')
    setMode(null)
    api.get(`/api/kluisjes/${kluisje.id}/geschiedenis`)
      .then(setGeschiedenis)
      .catch(() => setGeschiedenis([]))
  }, [kluisje.id])

  async function saveOpmerkingen() {
    try {
      setSavingStatus('saving')
      await api.put(`/api/kluisjes/${kluisje.id}`, { opmerkingen })
      setSavingStatus('saved')
      setTimeout(() => setSavingStatus(null), 1500)
    } catch {
      setSavingStatus('error')
    }
  }

  async function setStatus(status) {
    try {
      await api.put(`/api/kluisjes/${kluisje.id}`, { status })
      onUpdate()
    } catch (err) {
      alert(err.message)
    }
  }

  const isUitgeleend = detail.status === 'uitgeleend'
  const isVrij = detail.status === 'vrij'
  const isDefect = detail.status === 'defect'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />

      <div className="relative bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] flex flex-col overflow-hidden">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-700 bg-gradient-to-r from-slate-50 to-white dark:from-slate-800 dark:to-slate-800">
          <div>
            <h2 className="text-xl font-bold text-navy dark:text-white">{detail.kluisnummer}</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">{detail.cluster_naam} — {detail.locatie || 'Geen locatie'}</p>
          </div>
          <button onClick={onClose}
            className="w-9 h-9 flex items-center justify-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">

          {/* Sleutel niet ingeleverd warning */}
          {!!detail._sleutel_niet_ingeleverd && (
            <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-xl p-4 flex items-start gap-3">
              <span className="text-xl">🔑</span>
              <div className="flex-1">
                <div className="font-semibold text-red-800 dark:text-red-300">Sleutel niet ingeleverd</div>
                <div className="text-sm text-red-600 dark:text-red-400 mt-0.5">De vorige huurder heeft de sleutel nog niet teruggebracht.</div>
                <button
                  className="mt-2 px-3 py-1.5 bg-emerald-600 text-white text-sm rounded-lg hover:bg-emerald-700 transition-colors"
                  onClick={async () => {
                    const laatste = geschiedenis.find(g => !g.actief && !g.sleutel_ingeleverd)
                    if (laatste) {
                      await api.post(`/api/toewijzingen/${laatste.id}/sleutel-ingeleverd`, {})
                      onUpdate()
                    }
                  }}>
                  Sleutel is ingeleverd
                </button>
              </div>
            </div>
          )}

          {/* Borg niet teruggestort warning */}
          {!!detail._borg_niet_teruggestort && borgActiefVoor(detail.vestiging_id) && (
            <div className="bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-800 rounded-xl p-4 flex items-start gap-3">
              <span className="text-xl">💰</span>
              <div className="flex-1">
                <div className="font-semibold text-amber-800 dark:text-amber-300">Borg niet teruggestort</div>
                <div className="text-sm text-amber-600 dark:text-amber-400 mt-0.5">De borg van de vorige huurder is nog niet terugbetaald.</div>
                <button
                  className="mt-2 px-3 py-1.5 bg-emerald-600 text-white text-sm rounded-lg hover:bg-emerald-700 transition-colors"
                  onClick={async () => {
                    const laatste = geschiedenis.find(g => !g.actief && g.borg_betaald && !g.borg_teruggestort)
                    if (laatste) {
                      await api.post(`/api/toewijzingen/${laatste.id}/borg-teruggestort`, {})
                      onUpdate()
                    }
                  }}>
                  Borg is teruggestort
                </button>
              </div>
            </div>
          )}

          {/* Basic info */}
          <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4 text-sm">
            <InfoRow label="Sleutelnummer">{detail.sleutelnummer || '—'}</InfoRow>
            <InfoRow label="Status"><StatusBadge status={detail.status} sleutelNietIngeleverd={detail._sleutel_niet_ingeleverd} /></InfoRow>
          </div>

          {/* Huurder section */}
          {isUitgeleend && (
            <div className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-xl p-4">
              <div className="text-sm font-bold text-emerald-800 dark:text-emerald-300 mb-3 flex items-center gap-2">
                <span className="w-2.5 h-2.5 bg-emerald-500 rounded-full" />
                Huidige huurder
              </div>
              <div className="text-sm space-y-0">
                <InfoRow label="Naam"><span className="font-bold text-base text-slate-900 dark:text-slate-100">{detail.leerling_naam}</span></InfoRow>
                <InfoRow label="Stamnummer"><span className="text-base">{detail.leerling_stamnr || '—'}</span></InfoRow>
                <InfoRow label="Klas"><span className="text-base">{detail.leerling_klas || '—'}</span></InfoRow>
                {detail.periode_van && (
                  <InfoRow label="Periode">{formatDate(detail.periode_van)} t/m {formatDate(detail.periode_tot)}</InfoRow>
                )}
                {borgActiefVoor(detail.vestiging_id) && detail.borgbedrag != null && detail.borgbedrag > 0 && (
                  <InfoRow label="Borg">
                    <span className={detail.borg_betaald ? 'text-emerald-700 dark:text-emerald-400 font-semibold' : 'text-amber-600 dark:text-amber-400 font-bold'}>
                      €{Number(detail.borgbedrag).toFixed(2)}
                      {detail.borg_betaald ? ' (betaald)' : ' (NIET betaald)'}
                    </span>
                  </InfoRow>
                )}
              </div>
            </div>
          )}

          {/* Forms */}
          {mode === 'toewijzen' && (
            <AssignForm kluisje={detail} onDone={() => onUpdate()} onCancel={() => setMode(null)} />
          )}
          {mode === 'beeindigen' && (
            <EndRentalForm kluisje={detail} onDone={() => onUpdate()} onCancel={() => setMode(null)} />
          )}

          {/* Opmerkingen */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Opmerkingen</label>
              {savingStatus === 'saving' && <span className="text-xs text-blue-500">Opslaan...</span>}
              {savingStatus === 'saved' && <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">Opgeslagen!</span>}
              {savingStatus === 'error' && <span className="text-xs text-red-500">Fout bij opslaan</span>}
            </div>
            <textarea
              className="w-full border border-slate-200 dark:border-slate-600 rounded-xl px-4 py-3 text-sm resize-none bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-300 focus:border-blue-400 outline-none transition-all"
              rows={2}
              value={opmerkingen}
              onChange={e => setOpmerkingen(e.target.value)}
              onBlur={saveOpmerkingen}
              placeholder="Notities over dit kluisje..."
            />
          </div>

          {/* Geschiedenis */}
          {geschiedenis.length > 0 && (
            <div>
              <div className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">Geschiedenis</div>
              <div className="space-y-2">
                {geschiedenis.map((g, i) => (
                  <div key={i} className="border border-slate-200 dark:border-slate-600 rounded-xl p-3 bg-slate-50/50 dark:bg-slate-700/30 text-sm">
                    <div className="flex justify-between items-start">
                      <span className="font-semibold text-slate-800 dark:text-slate-200">{g.leerling_naam}</span>
                      <span className="text-slate-400 text-xs">{g.leerling_klas}</span>
                    </div>
                    <div className="text-slate-500 dark:text-slate-400 text-xs mt-1">{formatDate(g.periode_van)} t/m {formatDate(g.periode_tot || g.einddatum) || '...'}</div>
                    <div className="flex flex-wrap gap-2 mt-2 text-xs">
                      {borgActiefVoor(detail.vestiging_id) && g.borgbedrag > 0 && (
                        g.borg_teruggestort ? (
                          <span className="text-emerald-600 dark:text-emerald-400">
                            €{Number(g.borgbedrag).toFixed(0)} terug
                          </span>
                        ) : g.borg_betaald && !g.actief ? (
                          <button
                            className="px-2 py-0.5 bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400 rounded-lg hover:bg-emerald-100 dark:hover:bg-emerald-900/40 hover:text-emerald-700 dark:hover:text-emerald-400 transition-colors font-medium"
                            onClick={async () => {
                              await api.post(`/api/toewijzingen/${g.id}/borg-teruggestort`, {})
                              onUpdate()
                            }}>
                            €{Number(g.borgbedrag).toFixed(0)} niet terug ✓
                          </button>
                        ) : (
                          <span className="text-slate-400">
                            €{Number(g.borgbedrag).toFixed(0)} niet betaald
                          </span>
                        )
                      )}
                      <span className={g.sleutel_ingeleverd ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}>
                        🔑 {g.sleutel_ingeleverd ? 'Ingeleverd' : 'Niet ingeleverd'}
                      </span>
                    </div>
                    {g.opmerking && <div className="text-slate-500 dark:text-slate-400 mt-1.5 italic text-xs">{g.opmerking}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Action buttons footer */}
        {mode === null && (
          <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 flex flex-wrap gap-2">
            {isVrij && (
              <button onClick={() => setMode('toewijzen')}
                className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl py-3 text-sm font-bold hover:from-blue-700 hover:to-blue-800 transition-all shadow-sm">
                Toewijzen
              </button>
            )}
            {isUitgeleend && (
              <button onClick={() => setMode('beeindigen')}
                className="flex-1 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-xl py-3 text-sm font-bold hover:from-red-600 hover:to-red-700 transition-all shadow-sm">
                Huur beëindigen
              </button>
            )}
            {!isDefect ? (
              <button onClick={() => setStatus('defect')}
                className="border-2 border-amber-300 dark:border-amber-600 text-amber-700 dark:text-amber-400 rounded-xl px-5 py-3 text-sm font-medium hover:bg-amber-50 dark:hover:bg-amber-900/20 transition-colors">
                Markeer als defect
              </button>
            ) : (
              <button onClick={() => setStatus('vrij')}
                className="flex-1 bg-gradient-to-r from-sky-500 to-sky-600 text-white rounded-xl py-3 text-sm font-bold hover:from-sky-600 hover:to-sky-700 transition-all shadow-sm">
                Markeer als vrij
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
