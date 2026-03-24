import { useState, useEffect } from 'react'
import { api } from '../api'
import AssignForm from './AssignForm'
import EndRentalForm from './EndRentalForm'

export default function SidePanel({ kluisje, onClose, onUpdate }) {
  const [detail, setDetail] = useState(kluisje)
  const [geschiedenis, setGeschiedenis] = useState([])
  const [opmerkingen, setOpmerkingen] = useState(kluisje.opmerkingen || '')
  const [mode, setMode] = useState(null) // null | 'toewijzen' | 'beeindigen'
  const [savingStatus, setSavingStatus] = useState(null)

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

  function handleDone() {
    onUpdate()
  }

  const isUitgeleend = detail.status === 'uitgeleend'
  const isVrij = detail.status === 'vrij'
  const isDefect = detail.status === 'defect'

  return (
    <>
      {/* Mobile overlay backdrop */}
      <div className="fixed inset-0 bg-black/30 z-20 md:hidden" onClick={onClose} />

      <div className="fixed right-0 top-0 bottom-0 z-30 md:relative md:z-auto
        w-full max-w-sm md:w-80 lg:w-96
        bg-white border-l border-slate-200 flex flex-col shadow-xl md:shadow-none">

        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-slate-50">
          <button className="md:hidden text-slate-500 text-sm flex items-center gap-1" onClick={onClose}>
            ← Terug
          </button>
          <h2 className="font-bold text-navy text-base">Kluisje {detail.kluisnummer}</h2>
          <button className="hidden md:block text-slate-400 hover:text-slate-600 text-lg leading-none" onClick={onClose}>✕</button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">

          {/* Basic info */}
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Sleutelnr</span>
              <span className="font-medium">{detail.sleutelnummer || '—'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Cluster</span>
              <span className="font-medium">{detail.cluster_naam || '—'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Locatie</span>
              <span className="font-medium">{detail.locatie || '—'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-500">Status</span>
              <span className={`text-xs px-2 py-0.5 rounded ${
                isUitgeleend ? 'bg-green-100 text-green-600' :
                isDefect ? 'bg-amber-100 text-amber-600' :
                'bg-blue-100 text-blue-600'
              }`}>{detail.status}</span>
            </div>
          </div>

          {/* Sleutel niet ingeleverd warning */}
          {detail._sleutel_niet_ingeleverd && (
            <div className="bg-red-50 border border-red-200 rounded p-2 text-xs text-red-600 flex items-center gap-2">
              <span>⚠</span> Sleutel nog niet ingeleverd van vorige huur
            </div>
          )}

          {/* Huurder section */}
          {isUitgeleend && (
            <div className="bg-green-50 border border-green-200 rounded p-3 space-y-1 text-sm">
              <div className="text-xs font-semibold text-green-700 mb-2">Huidige huurder</div>
              <div className="flex justify-between">
                <span className="text-slate-500">Naam</span>
                <span className="font-medium">{detail.leerling_naam}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Stamnr</span>
                <span>{detail.leerling_stamnr || '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Klas</span>
                <span>{detail.leerling_klas || '—'}</span>
              </div>
              {detail.periode_van && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Periode</span>
                  <span className="text-xs">{detail.periode_van} t/m {detail.periode_tot}</span>
                </div>
              )}
              {detail.borgbedrag != null && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Borg</span>
                  <span>€{Number(detail.borgbedrag).toFixed(2)}{detail.borg_betaald ? ' ✓' : ' (niet betaald)'}</span>
                </div>
              )}
            </div>
          )}

          {/* Opmerkingen */}
          <div>
            <label className="block text-xs text-slate-500 mb-1">
              Opmerkingen
              {savingStatus === 'saving' && <span className="ml-2 text-blue-400">Opslaan...</span>}
              {savingStatus === 'saved' && <span className="ml-2 text-green-500">Opgeslagen</span>}
              {savingStatus === 'error' && <span className="ml-2 text-red-500">Fout bij opslaan</span>}
            </label>
            <textarea
              className="w-full border rounded px-2 py-1 text-sm resize-none"
              rows={3}
              value={opmerkingen}
              onChange={e => setOpmerkingen(e.target.value)}
              onBlur={saveOpmerkingen}
            />
          </div>

          {/* Forms */}
          {mode === 'toewijzen' && (
            <AssignForm kluisje={detail} onDone={handleDone} onCancel={() => setMode(null)} />
          )}
          {mode === 'beeindigen' && (
            <EndRentalForm kluisje={detail} onDone={handleDone} onCancel={() => setMode(null)} />
          )}

          {/* Geschiedenis */}
          {geschiedenis.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-slate-500 mb-2">Geschiedenis</div>
              <div className="space-y-2">
                {geschiedenis.map((g, i) => (
                  <div key={i} className="text-xs border rounded p-2 bg-slate-50">
                    <div className="font-medium">{g.leerling_naam}</div>
                    <div className="text-slate-400">{g.periode_van} t/m {g.periode_tot || g.einddatum || '…'}</div>
                    {g.opmerking && <div className="text-slate-500 mt-1">{g.opmerking}</div>}
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
                className="w-full bg-navy text-white rounded py-2 text-sm hover:bg-navy/90">
                Toewijzen
              </button>
            )}
            {isUitgeleend && (
              <button onClick={() => setMode('beeindigen')}
                className="w-full bg-red-600 text-white rounded py-2 text-sm hover:bg-red-700">
                Huur beëindigen
              </button>
            )}
            {!isDefect && (
              <button onClick={() => setStatus('defect')}
                className="w-full border border-amber-400 text-amber-600 rounded py-2 text-sm hover:bg-amber-50">
                Markeer als defect
              </button>
            )}
            {isDefect && (
              <button onClick={() => setStatus('vrij')}
                className="w-full border border-blue-400 text-blue-600 rounded py-2 text-sm hover:bg-blue-50">
                Markeer als vrij
              </button>
            )}
          </div>
        )}
      </div>
    </>
  )
}
