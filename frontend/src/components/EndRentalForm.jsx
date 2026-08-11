import { useState } from 'react'
import { api } from '../api'
import { useInstellingen } from '../context/InstellingenContext'

function today() {
  return new Date().toISOString().slice(0, 10)
}

export default function EndRentalForm({ kluisje, onDone, onCancel }) {
  const [borgTeruggestort, setBorgTeruggestort] = useState(false)
  const [einddatum, setEinddatum] = useState(today())
  const [opmerking, setOpmerking] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const { borgActiefVoor } = useInstellingen()

  const toewijzingId = kluisje.toewijzing_id

  // The key question IS the confirm action: one click both answers it and ends
  // the huur. A pre-ticked checkbox would be just as fast but nobody reads a
  // default, and this flag ends up in the audit trail.
  async function beeindig(sleutelIngeleverd) {
    if (!toewijzingId) { setError('Geen actieve toewijzing gevonden.'); return }
    setLoading(true)
    setError('')
    try {
      await api.post(`/api/toewijzingen/${toewijzingId}/beeindigen`, {
        sleutel_ingeleverd: sleutelIngeleverd,
        borg_teruggestort: borgTeruggestort,
        einddatum,
        opmerking,
      })
      onDone()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-3 mt-3">
      {borgActiefVoor(kluisje.vestiging_id) && (
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" checked={borgTeruggestort} onChange={e => setBorgTeruggestort(e.target.checked)} />
          Borg teruggestort
        </label>
      )}
      <div>
        <label className="block text-xs text-slate-500 mb-1">Einddatum</label>
        <input type="date" className="w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 dark:text-white rounded px-2 py-1 text-sm" value={einddatum}
          onChange={e => setEinddatum(e.target.value)} />
      </div>
      <div>
        <label className="block text-xs text-slate-500 mb-1">Opmerking</label>
        <textarea className="w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 dark:text-white rounded px-2 py-1 text-sm" rows={3} value={opmerking}
          onChange={e => setOpmerking(e.target.value)} placeholder="Optionele opmerking..." />
      </div>
      {error && <p className="text-red-500 text-xs">{error}</p>}

      <div className="pt-1 border-t border-slate-200 dark:border-slate-700">
        <p className="text-sm font-semibold text-navy dark:text-white mt-2 mb-2">Is de sleutel ingeleverd?</p>
        <div className="flex gap-2">
          <button type="button" disabled={loading} onClick={() => beeindig(true)}
            className="flex-1 bg-emerald-600 text-white rounded-lg py-2 text-sm font-semibold hover:bg-emerald-700 disabled:opacity-50 transition-colors">
            {loading ? 'Bezig...' : 'Ja, beëindigen'}
          </button>
          <button type="button" disabled={loading} onClick={() => beeindig(false)}
            className="flex-1 border-2 border-red-400 text-red-600 dark:text-red-400 rounded-lg py-2 text-sm font-semibold hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50 transition-colors">
            {loading ? 'Bezig...' : 'Nee, beëindigen'}
          </button>
        </div>
        <button type="button" onClick={onCancel} disabled={loading}
          className="w-full mt-2 py-1.5 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200">
          Annuleren
        </button>
      </div>
    </div>
  )
}
