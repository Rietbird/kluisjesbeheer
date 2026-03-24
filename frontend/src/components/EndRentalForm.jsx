import { useState } from 'react'
import { api } from '../api'

function today() {
  return new Date().toISOString().slice(0, 10)
}

export default function EndRentalForm({ kluisje, onDone, onCancel }) {
  const [sleutelIngeleverd, setSleutelIngeleverd] = useState(false)
  const [borgTeruggestort, setBorgTeruggestort] = useState(false)
  const [einddatum, setEinddatum] = useState(today())
  const [opmerking, setOpmerking] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const toewijzingId = kluisje.toewijzing_id

  async function handleSubmit(e) {
    e.preventDefault()
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
    <form onSubmit={handleSubmit} className="space-y-3 mt-3">
      <label className="flex items-center gap-2 text-sm cursor-pointer">
        <input type="checkbox" checked={sleutelIngeleverd} onChange={e => setSleutelIngeleverd(e.target.checked)} />
        Sleutel ingeleverd
      </label>
      <label className="flex items-center gap-2 text-sm cursor-pointer">
        <input type="checkbox" checked={borgTeruggestort} onChange={e => setBorgTeruggestort(e.target.checked)} />
        Borg teruggestort
      </label>
      <div>
        <label className="block text-xs text-slate-500 mb-1">Einddatum</label>
        <input type="date" className="w-full border rounded px-2 py-1 text-sm" value={einddatum}
          onChange={e => setEinddatum(e.target.value)} />
      </div>
      <div>
        <label className="block text-xs text-slate-500 mb-1">Opmerking</label>
        <textarea className="w-full border rounded px-2 py-1 text-sm" rows={3} value={opmerking}
          onChange={e => setOpmerking(e.target.value)} placeholder="Optionele opmerking..." />
      </div>
      {error && <p className="text-red-500 text-xs">{error}</p>}
      <div className="flex gap-2">
        <button type="submit" disabled={loading}
          className="flex-1 bg-red-600 text-white rounded py-1.5 text-sm hover:bg-red-700 disabled:opacity-50">
          {loading ? 'Bezig...' : 'Bevestigen'}
        </button>
        <button type="button" onClick={onCancel}
          className="flex-1 border rounded py-1.5 text-sm text-slate-500 hover:bg-slate-50">
          Annuleren
        </button>
      </div>
    </form>
  )
}
