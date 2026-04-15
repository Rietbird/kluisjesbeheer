import { useState, useEffect } from 'react'
import { api } from '../api'
import AssignForm from './AssignForm'
import EndRentalForm from './EndRentalForm'
import { useInstellingen } from '../context/InstellingenContext'
import { formatDate } from '../utils/formatDate'

function InfoRow({ label, children }) {
  return (
    <div className="flex justify-between items-center py-1">
      <span className="text-slate-500 text-xs">{label}</span>
      <span className="text-sm font-medium text-right">{children}</span>
    </div>
  )
}

function StatusBadge({ status, sleutelNietIngeleverd }) {
  const cls = status === 'uitgeleend' ? 'bg-sky-100 text-sky-700'
    : status === 'defect' ? 'bg-amber-100 text-amber-700'
    : sleutelNietIngeleverd ? 'bg-red-100 text-red-700'
    : 'bg-emerald-100 text-emerald-700'
  return <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${cls}`}>{status}</span>
}

export default function SidePanel({ kluisje, onClose, onUpdate }) {
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
    <>
      <div className="fixed inset-0 bg-black/30 z-20 md:hidden" onClick={onClose} />

      <div className="fixed right-0 top-0 bottom-0 z-30 md:relative md:z-auto
        w-full max-w-sm md:w-80 lg:w-96
        bg-white border-l border-slate-200 flex flex-col shadow-xl md:shadow-none">

        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-slate-50">
          <button className="md:hidden text-slate-500 text-sm flex items-center gap-1" onClick={onClose}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Terug
          </button>
          <h2 className="font-bold text-navy text-base">{detail.kluisnummer}</h2>
          <button className="hidden md:block text-slate-400 hover:text-slate-600 p-1 rounded hover:bg-slate-100" onClick={onClose}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">

          {/* Basic info */}
          <div className="bg-slate-50 rounded-lg p-3 divide-y divide-slate-200">
            <InfoRow label="Sleutelnr">{detail.sleutelnummer || '—'}</InfoRow>
            <InfoRow label="Cluster">{detail.cluster_naam || '—'}</InfoRow>
            <InfoRow label="Locatie">{detail.locatie || '—'}</InfoRow>
            <InfoRow label="Status"><StatusBadge status={detail.status} sleutelNietIngeleverd={detail._sleutel_niet_ingeleverd} /></InfoRow>
          </div>

          {/* Sleutel niet ingeleverd warning */}
          {detail._sleutel_niet_ingeleverd && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2">
              <span className="text-red-500 text-base mt-0.5">🔑</span>
              <div className="flex-1">
                <div className="text-sm font-medium text-red-700">Sleutel niet ingeleverd</div>
                <div className="text-xs text-red-600 mt-0.5">De vorige huurder heeft de sleutel nog niet teruggebracht.</div>
                {geschiedenis.length > 0 && !geschiedenis[0].sleutel_ingeleverd && (
                  <button onClick={async () => { await api.post(`/api/toewijzingen/${geschiedenis[0].id}/sleutel-ingeleverd`); onUpdate() }}
                    className="mt-2 text-xs bg-white border border-red-300 text-red-700 px-3 py-1 rounded hover:bg-red-50 font-medium">
                    Markeer als ingeleverd
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Borg niet teruggestort warning */}
          {detail._borg_niet_teruggestort && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-2">
              <span className="text-amber-500 text-base mt-0.5">💰</span>
              <div className="flex-1">
                <div className="text-sm font-medium text-amber-700">Borg niet teruggestort</div>
                <div className="text-xs text-amber-600 mt-0.5">De borg van de vorige huurder is nog niet teruggestort.</div>
                {geschiedenis.length > 0 && !geschiedenis[0].borg_teruggestort && geschiedenis[0].borg_betaald && (
                  <button onClick={async () => { await api.post(`/api/toewijzingen/${geschiedenis[0].id}/borg-teruggestort`); onUpdate() }}
                    className="mt-2 text-xs bg-white border border-amber-300 text-amber-700 px-3 py-1 rounded hover:bg-amber-50 font-medium">
                    Markeer als teruggestort
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Huurder section */}
          {isUitgeleend && (
            <div className="bg-sky-50 border border-sky-200 rounded-lg p-3 space-y-0.5">
              <div className="text-xs font-semibold text-sky-700 mb-2 flex items-center gap-1.5">
                <span className="w-2 h-2 bg-sky-500 rounded-full" />
                Huidige huurder
              </div>
              <InfoRow label="Naam"><span className="font-semibold">{detail.leerling_naam}</span>{detail.leerling_vertrokken_op && <span className="ml-2 text-xs text-red-600 font-bold bg-red-50 px-1.5 py-0.5 rounded">Vertrokken</span>}</InfoRow>
              <InfoRow label="Stamnr">{detail.leerling_stamnr || '—'}</InfoRow>
              <InfoRow label="Klas">{detail.leerling_klas || '—'}</InfoRow>
              {detail.periode_van && (
                <InfoRow label="Periode">
                  <span className="text-xs">{formatDate(detail.periode_van)} t/m {formatDate(detail.periode_tot)}</span>
                </InfoRow>
              )}
              {borgActiefVoor(detail.vestiging_id) && detail.borgbedrag != null && (
                <InfoRow label="Borg">
                  <span className={detail.borg_betaald ? 'text-green-700' : 'text-amber-600 font-semibold'}>
                    €{Number(detail.borgbedrag).toFixed(2)}
                    {detail.borg_betaald ? ' (betaald)' : ' (niet betaald)'}
                  </span>
                </InfoRow>
              )}
            </div>
          )}

          {/* Opmerkingen */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-slate-600">Opmerkingen</label>
              {savingStatus === 'saving' && <span className="text-xs text-blue-400">Opslaan...</span>}
              {savingStatus === 'saved' && <span className="text-xs text-green-500">Opgeslagen</span>}
              {savingStatus === 'error' && <span className="text-xs text-red-500">Fout</span>}
            </div>
            <textarea
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm resize-none focus:ring-2 focus:ring-navy/20 focus:border-navy outline-none"
              rows={2}
              value={opmerkingen}
              onChange={e => setOpmerkingen(e.target.value)}
              onBlur={saveOpmerkingen}
              placeholder="Notities over dit kluisje..."
            />
          </div>

          {/* Forms */}
          {mode === 'toewijzen' && (
            <AssignForm kluisje={detail} onDone={() => onUpdate()} onCancel={() => setMode(null)} />
          )}
          {mode === 'beeindigen' && (
            <EndRentalForm kluisje={detail} onDone={() => onUpdate()} onCancel={() => setMode(null)} />
          )}

          {/* Geschiedenis */}
          {geschiedenis.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-slate-600 mb-2">Geschiedenis</div>
              <div className="space-y-1.5">
                {geschiedenis.map((g, i) => (
                  <div key={i} className="text-xs border border-slate-200 rounded-lg p-2.5 bg-slate-50/50">
                    <div className="flex justify-between items-start">
                      <span className="font-medium text-slate-800">{g.leerling_naam}</span>
                      <span className="text-slate-400">{g.leerling_klas}</span>
                    </div>
                    <div className="text-slate-400 mt-0.5">{formatDate(g.periode_van)} t/m {formatDate(g.periode_tot || g.einddatum) || '...'}</div>
                    <div className="flex gap-3 mt-1.5">
                      {borgActiefVoor(detail.vestiging_id) && g.borgbedrag > 0 && (
                        <span className={g.borg_teruggestort ? 'text-green-600' : g.borg_betaald ? 'text-amber-600' : 'text-slate-400'}>
                          €{Number(g.borgbedrag).toFixed(0)}
                          {g.borg_teruggestort ? ' terug' : g.borg_betaald ? ' niet terug' : ' niet betaald'}
                        </span>
                      )}
                      <span className={g.sleutel_ingeleverd ? 'text-green-600' : 'text-red-600'}>
                        🔑 {g.sleutel_ingeleverd ? 'Ingeleverd' : 'Niet ingeleverd'}
                      </span>
                    </div>
                    {g.opmerking && <div className="text-slate-500 mt-1 italic">{g.opmerking}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Action buttons */}
        {mode === null && (
          <div className="p-4 border-t border-slate-200 space-y-2">
            {isVrij && (
              <button onClick={() => setMode('toewijzen')}
                className="w-full bg-navy text-white rounded-lg py-2.5 text-sm font-medium hover:bg-navy/90 transition-colors">
                Toewijzen
              </button>
            )}
            {isUitgeleend && (
              <button onClick={() => setMode('beeindigen')}
                className="w-full bg-red-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-red-700 transition-colors">
                Huur beëindigen
              </button>
            )}
            {!isDefect ? (
              <button onClick={() => setStatus('defect')}
                className="w-full border border-amber-300 text-amber-700 rounded-lg py-2 text-sm hover:bg-amber-50 transition-colors">
                Markeer als defect
              </button>
            ) : (
              <button onClick={() => setStatus('vrij')}
                className="w-full border border-emerald-300 text-emerald-700 rounded-lg py-2 text-sm hover:bg-emerald-50 transition-colors">
                Markeer als vrij
              </button>
            )}
          </div>
        )}
      </div>
    </>
  )
}
