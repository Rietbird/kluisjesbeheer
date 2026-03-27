import { useState, useEffect, useRef } from 'react'
import { api } from '../api'
import { useInstellingen } from '../context/InstellingenContext'

export default function AssignForm({ kluisje, onDone, onCancel }) {
  const [q, setQ] = useState('')
  const [results, setResults] = useState([])
  const [selected, setSelected] = useState(null)
  const [showDropdown, setShowDropdown] = useState(false)
  const [periodeVan, setPeriodeVan] = useState('')
  const [periodeTot, setPeriodeTot] = useState('')
  const [borgbedrag, setBorgbedrag] = useState('')
  const [borgBetaald, setBorgBetaald] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const debounceRef = useRef(null)

  const { borgActief } = useInstellingen()

  useEffect(() => {
    if (q.length < 2) { setResults([]); setShowDropdown(false); return }
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      api.get(`/api/magister/leerlingen?q=${encodeURIComponent(q)}`)
        .then(data => { setResults(data); setShowDropdown(true) })
        .catch(() => setResults([]))
    }, 300)
    return () => clearTimeout(debounceRef.current)
  }, [q])

  function selectLeerling(l) {
    setSelected(l)
    setQ(l.naam || l.leerling_naam || '')
    setShowDropdown(false)
    setResults([])
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!selected) { setError('Kies een leerling.'); return }
    if (!periodeVan || !periodeTot) { setError('Vul de periode in.'); return }
    setLoading(true)
    setError('')
    try {
      await api.post(`/api/kluisjes/${kluisje.id}/toewijzen`, {
        leerling_stamnr: selected.stamnr || selected.leerling_stamnr,
        leerling_naam: selected.naam || selected.leerling_naam,
        leerling_klas: selected.klas || selected.leerling_klas,
        periode_van: periodeVan,
        periode_tot: periodeTot,
        borgbedrag: borgbedrag ? Number(borgbedrag) : null,
        borg_betaald: borgBetaald,
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
      <div className="relative">
        <label className="block text-xs text-slate-500 mb-1">Leerling</label>
        <input
          className="w-full border rounded px-2 py-1 text-sm"
          placeholder="Zoek op naam of stamnr..."
          value={q}
          onChange={e => { setQ(e.target.value); setSelected(null) }}
          autoComplete="off"
        />
        {showDropdown && results.length > 0 && (
          <div className="absolute z-10 w-full bg-white border border-slate-200 rounded shadow-lg max-h-40 overflow-y-auto">
            {results.map((l, i) => (
              <button key={i} type="button"
                className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 border-b last:border-b-0"
                onClick={() => selectLeerling(l)}>
                <span className="font-medium">{l.naam || l.leerling_naam}</span>
                <span className="text-slate-400 ml-2 text-xs">{l.stamnr || l.leerling_stamnr}</span>
                <span className="text-slate-400 ml-2 text-xs">{l.klas || l.leerling_klas}</span>
              </button>
            ))}
          </div>
        )}
      </div>
      {selected && (
        <div className="bg-blue-50 rounded p-2 text-xs space-y-1">
          <div><span className="text-slate-500">Naam:</span> <span className="font-medium">{selected.naam || selected.leerling_naam}</span></div>
          <div><span className="text-slate-500">Stamnr:</span> {selected.stamnr || selected.leerling_stamnr}</div>
          <div><span className="text-slate-500">Klas:</span> {selected.klas || selected.leerling_klas}</div>
        </div>
      )}
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-xs text-slate-500 mb-1">Periode van</label>
          <input type="date" className="w-full border rounded px-2 py-1 text-sm" value={periodeVan}
            onChange={e => setPeriodeVan(e.target.value)} />
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">Periode tot</label>
          <input type="date" className="w-full border rounded px-2 py-1 text-sm" value={periodeTot}
            onChange={e => setPeriodeTot(e.target.value)} />
        </div>
      </div>
      {borgActief && (
        <>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Borgbedrag (€)</label>
            <input type="number" step="0.01" className="w-full border rounded px-2 py-1 text-sm" value={borgbedrag}
              onChange={e => setBorgbedrag(e.target.value)} placeholder="0.00" />
          </div>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="checkbox" checked={borgBetaald} onChange={e => setBorgBetaald(e.target.checked)} />
            Borg betaald
          </label>
        </>
      )}
      {error && <p className="text-red-500 text-xs">{error}</p>}
      <div className="flex gap-2">
        <button type="submit" disabled={loading}
          className="flex-1 bg-navy text-white rounded py-1.5 text-sm hover:bg-navy/90 disabled:opacity-50">
          {loading ? 'Bezig...' : 'Toewijzen'}
        </button>
        <button type="button" onClick={onCancel}
          className="flex-1 border rounded py-1.5 text-sm text-slate-500 hover:bg-slate-50">
          Annuleren
        </button>
      </div>
    </form>
  )
}
