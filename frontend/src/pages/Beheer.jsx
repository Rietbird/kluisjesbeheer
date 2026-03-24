import { useState, useEffect } from 'react'
import { api } from '../api'

function ConfirmButton({ onConfirm, children, className }) {
  const [confirming, setConfirming] = useState(false)
  if (confirming) {
    return (
      <span className="flex gap-1">
        <button onClick={() => { setConfirming(false); onConfirm() }}
          className="text-xs px-2 py-1 bg-red-500 text-white rounded hover:bg-red-600">Ja</button>
        <button onClick={() => setConfirming(false)}
          className="text-xs px-2 py-1 border rounded text-slate-500 hover:bg-slate-50">Nee</button>
      </span>
    )
  }
  return (
    <button onClick={() => setConfirming(true)} className={className}>{children}</button>
  )
}

// ── Vestigingen ──────────────────────────────────────────────────────────────

function VestigingenPanel({ onSelect, selectedId }) {
  const [vestigingen, setVestigingen] = useState([])
  const [naam, setNaam] = useState('')
  const [adres, setAdres] = useState('')
  const [editId, setEditId] = useState(null)
  const [editNaam, setEditNaam] = useState('')
  const [editAdres, setEditAdres] = useState('')
  const [error, setError] = useState('')

  function load() {
    api.get('/api/vestigingen').then(setVestigingen).catch(() => {})
  }

  useEffect(() => { load() }, [])

  async function handleAdd(e) {
    e.preventDefault()
    setError('')
    try {
      await api.post('/api/vestigingen', { naam, adres })
      setNaam(''); setAdres('')
      load()
    } catch (err) { setError(err.message) }
  }

  async function handleUpdate(id) {
    setError('')
    try {
      await api.put(`/api/vestigingen/${id}`, { naam: editNaam, adres: editAdres })
      setEditId(null)
      load()
    } catch (err) { setError(err.message) }
  }

  async function handleDelete(id) {
    setError('')
    try {
      await api.del(`/api/vestigingen/${id}`)
      if (selectedId === id) onSelect(null)
      load()
    } catch (err) { setError(err.message) }
  }

  function startEdit(v) {
    setEditId(v.id); setEditNaam(v.naam); setEditAdres(v.adres || '')
  }

  return (
    <div>
      <h2 className="text-sm font-bold text-navy mb-3">Vestigingen</h2>
      {error && <p className="text-red-500 text-xs mb-2">{error}</p>}
      <div className="space-y-1 mb-4">
        {vestigingen.map(v => (
          <div key={v.id}
            className={`border rounded p-2 cursor-pointer text-sm ${selectedId === v.id ? 'border-navy bg-navy/5' : 'hover:bg-slate-50'}`}>
            {editId === v.id ? (
              <div className="space-y-1">
                <input className="w-full border rounded px-2 py-1 text-xs" value={editNaam}
                  onChange={e => setEditNaam(e.target.value)} placeholder="Naam" />
                <input className="w-full border rounded px-2 py-1 text-xs" value={editAdres}
                  onChange={e => setEditAdres(e.target.value)} placeholder="Adres" />
                <div className="flex gap-1 mt-1">
                  <button onClick={() => handleUpdate(v.id)}
                    className="text-xs px-2 py-1 bg-navy text-white rounded hover:bg-navy/90">Opslaan</button>
                  <button onClick={() => setEditId(null)}
                    className="text-xs px-2 py-1 border rounded text-slate-500 hover:bg-slate-50">Annuleren</button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between" onClick={() => onSelect(v.id)}>
                <div>
                  <div className="font-medium">{v.naam}</div>
                  {v.adres && <div className="text-xs text-slate-400">{v.adres}</div>}
                </div>
                <div className="flex gap-1" onClick={e => e.stopPropagation()}>
                  <button onClick={() => startEdit(v)}
                    className="text-xs text-slate-400 hover:text-navy px-1">✎</button>
                  <ConfirmButton onConfirm={() => handleDelete(v.id)}
                    className="text-xs text-slate-400 hover:text-red-500 px-1">✕</ConfirmButton>
                </div>
              </div>
            )}
          </div>
        ))}
        {vestigingen.length === 0 && <p className="text-xs text-slate-400">Nog geen vestigingen.</p>}
      </div>
      <form onSubmit={handleAdd} className="space-y-1">
        <div className="text-xs font-semibold text-slate-500 mb-1">Nieuwe vestiging</div>
        <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Naam" value={naam}
          onChange={e => setNaam(e.target.value)} required />
        <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Adres (optioneel)" value={adres}
          onChange={e => setAdres(e.target.value)} />
        <button type="submit"
          className="w-full bg-navy text-white rounded py-1.5 text-sm hover:bg-navy/90 mt-1">
          + Toevoegen
        </button>
      </form>
    </div>
  )
}

// ── Clusters ─────────────────────────────────────────────────────────────────

function ClustersPanel({ vestigingId, onSelect, selectedId }) {
  const [clusters, setClusters] = useState([])
  const [naam, setNaam] = useState('')
  const [borg, setBorg] = useState('')
  const [editId, setEditId] = useState(null)
  const [editNaam, setEditNaam] = useState('')
  const [editBorg, setEditBorg] = useState('')
  const [error, setError] = useState('')

  function load() {
    if (!vestigingId) { setClusters([]); return }
    api.get(`/api/vestigingen/${vestigingId}/clusters`).then(setClusters).catch(() => {})
  }

  useEffect(() => { load() }, [vestigingId])

  async function handleAdd(e) {
    e.preventDefault()
    setError('')
    try {
      await api.post('/api/clusters', { vestiging_id: vestigingId, naam, standaard_borg: borg ? Number(borg) : null })
      setNaam(''); setBorg('')
      load()
    } catch (err) { setError(err.message) }
  }

  async function handleUpdate(id) {
    setError('')
    try {
      await api.put(`/api/clusters/${id}`, { naam: editNaam, standaard_borg: editBorg ? Number(editBorg) : null })
      setEditId(null)
      load()
    } catch (err) { setError(err.message) }
  }

  async function handleDelete(id) {
    setError('')
    try {
      await api.del(`/api/clusters/${id}`)
      if (selectedId === id) onSelect(null)
      load()
    } catch (err) { setError(err.message) }
  }

  if (!vestigingId) return (
    <div>
      <h2 className="text-sm font-bold text-navy mb-3">Clusters</h2>
      <p className="text-xs text-slate-400">Selecteer een vestiging.</p>
    </div>
  )

  return (
    <div>
      <h2 className="text-sm font-bold text-navy mb-3">Clusters</h2>
      {error && <p className="text-red-500 text-xs mb-2">{error}</p>}
      <div className="space-y-1 mb-4">
        {clusters.map(c => (
          <div key={c.id}
            className={`border rounded p-2 cursor-pointer text-sm ${selectedId === c.id ? 'border-navy bg-navy/5' : 'hover:bg-slate-50'}`}>
            {editId === c.id ? (
              <div className="space-y-1">
                <input className="w-full border rounded px-2 py-1 text-xs" value={editNaam}
                  onChange={e => setEditNaam(e.target.value)} placeholder="Naam" />
                <input type="number" step="0.01" className="w-full border rounded px-2 py-1 text-xs" value={editBorg}
                  onChange={e => setEditBorg(e.target.value)} placeholder="Standaard borg (€)" />
                <div className="flex gap-1 mt-1">
                  <button onClick={() => handleUpdate(c.id)}
                    className="text-xs px-2 py-1 bg-navy text-white rounded">Opslaan</button>
                  <button onClick={() => setEditId(null)}
                    className="text-xs px-2 py-1 border rounded text-slate-500">Annuleren</button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between" onClick={() => onSelect(c.id)}>
                <div>
                  <div className="font-medium">{c.naam}</div>
                  {c.standaard_borg != null && <div className="text-xs text-slate-400">Borg: €{Number(c.standaard_borg).toFixed(2)}</div>}
                </div>
                <div className="flex gap-1" onClick={e => e.stopPropagation()}>
                  <button onClick={() => { setEditId(c.id); setEditNaam(c.naam); setEditBorg(c.standaard_borg ?? '') }}
                    className="text-xs text-slate-400 hover:text-navy px-1">✎</button>
                  <ConfirmButton onConfirm={() => handleDelete(c.id)}
                    className="text-xs text-slate-400 hover:text-red-500 px-1">✕</ConfirmButton>
                </div>
              </div>
            )}
          </div>
        ))}
        {clusters.length === 0 && <p className="text-xs text-slate-400">Nog geen clusters voor deze vestiging.</p>}
      </div>
      <form onSubmit={handleAdd} className="space-y-1">
        <div className="text-xs font-semibold text-slate-500 mb-1">Nieuw cluster</div>
        <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Naam" value={naam}
          onChange={e => setNaam(e.target.value)} required />
        <input type="number" step="0.01" className="w-full border rounded px-2 py-1 text-sm"
          placeholder="Standaard borg (€)" value={borg} onChange={e => setBorg(e.target.value)} />
        <button type="submit"
          className="w-full bg-navy text-white rounded py-1.5 text-sm hover:bg-navy/90 mt-1">
          + Toevoegen
        </button>
      </form>
    </div>
  )
}

// ── Kluisjes ─────────────────────────────────────────────────────────────────

function KluisjesPanel({ clusterId }) {
  const [kluisjes, setKluisjes] = useState([])
  const [kluisnummer, setKluisnummer] = useState('')
  const [sleutelnummer, setSleutelnummer] = useState('')
  const [locatie, setLocatie] = useState('')
  const [editId, setEditId] = useState(null)
  const [editData, setEditData] = useState({})
  const [error, setError] = useState('')

  function load() {
    if (!clusterId) { setKluisjes([]); return }
    api.get(`/api/clusters/${clusterId}/kluisjes`).then(setKluisjes).catch(() => {})
  }

  useEffect(() => { load() }, [clusterId])

  async function handleAdd(e) {
    e.preventDefault()
    setError('')
    try {
      await api.post(`/api/clusters/${clusterId}/kluisjes`, { kluisnummer, sleutelnummer, locatie })
      setKluisnummer(''); setSleutelnummer(''); setLocatie('')
      load()
    } catch (err) { setError(err.message) }
  }

  async function handleUpdate(id) {
    setError('')
    try {
      await api.put(`/api/kluisjes/${id}`, { sleutelnummer: editData.sleutelnummer, locatie: editData.locatie })
      setEditId(null)
      load()
    } catch (err) { setError(err.message) }
  }

  async function handleDelete(id) {
    setError('')
    try {
      await api.del(`/api/kluisjes/${id}`)
      load()
    } catch (err) { setError(err.message) }
  }

  if (!clusterId) return (
    <div>
      <h2 className="text-sm font-bold text-navy mb-3">Kluisjes</h2>
      <p className="text-xs text-slate-400">Selecteer een cluster.</p>
    </div>
  )

  return (
    <div>
      <h2 className="text-sm font-bold text-navy mb-3">Kluisjes</h2>
      {error && <p className="text-red-500 text-xs mb-2">{error}</p>}
      <div className="space-y-1 mb-4 max-h-80 overflow-y-auto">
        {kluisjes.map(k => (
          <div key={k.id} className="border rounded p-2 text-sm hover:bg-slate-50">
            {editId === k.id ? (
              <div className="space-y-1">
                <div className="text-xs font-semibold">Kluisje {k.kluisnummer}</div>
                <input className="w-full border rounded px-2 py-1 text-xs" value={editData.sleutelnummer || ''}
                  onChange={e => setEditData(d => ({ ...d, sleutelnummer: e.target.value }))} placeholder="Sleutelnr" />
                <input className="w-full border rounded px-2 py-1 text-xs" value={editData.locatie || ''}
                  onChange={e => setEditData(d => ({ ...d, locatie: e.target.value }))} placeholder="Locatie" />
                <div className="flex gap-1 mt-1">
                  <button onClick={() => handleUpdate(k.id)}
                    className="text-xs px-2 py-1 bg-navy text-white rounded">Opslaan</button>
                  <button onClick={() => setEditId(null)}
                    className="text-xs px-2 py-1 border rounded text-slate-500">Annuleren</button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-medium text-navy">{k.kluisnummer}</span>
                  {k.sleutelnummer && <span className="text-xs text-slate-400 ml-2">sleutel {k.sleutelnummer}</span>}
                  {k.locatie && <span className="text-xs text-slate-400 ml-2">{k.locatie}</span>}
                  <span className={`ml-2 text-xs px-1.5 py-0.5 rounded ${
                    k.status === 'uitgeleend' ? 'bg-green-100 text-green-600' :
                    k.status === 'defect' ? 'bg-amber-100 text-amber-600' :
                    'bg-blue-100 text-blue-600'
                  }`}>{k.status}</span>
                </div>
                <div className="flex gap-1">
                  <button onClick={() => { setEditId(k.id); setEditData({ sleutelnummer: k.sleutelnummer || '', locatie: k.locatie || '' }) }}
                    className="text-xs text-slate-400 hover:text-navy px-1">✎</button>
                  <ConfirmButton onConfirm={() => handleDelete(k.id)}
                    className="text-xs text-slate-400 hover:text-red-500 px-1">✕</ConfirmButton>
                </div>
              </div>
            )}
          </div>
        ))}
        {kluisjes.length === 0 && <p className="text-xs text-slate-400">Nog geen kluisjes in dit cluster.</p>}
      </div>
      <form onSubmit={handleAdd} className="space-y-1">
        <div className="text-xs font-semibold text-slate-500 mb-1">Nieuw kluisje</div>
        <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Kluisnummer" value={kluisnummer}
          onChange={e => setKluisnummer(e.target.value)} required />
        <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Sleutelnummer (optioneel)"
          value={sleutelnummer} onChange={e => setSleutelnummer(e.target.value)} />
        <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Locatie (optioneel)"
          value={locatie} onChange={e => setLocatie(e.target.value)} />
        <button type="submit"
          className="w-full bg-navy text-white rounded py-1.5 text-sm hover:bg-navy/90 mt-1">
          + Toevoegen
        </button>
      </form>
    </div>
  )
}

// ── Beheer Page ───────────────────────────────────────────────────────────────

export default function Beheer() {
  const [selectedVestiging, setSelectedVestiging] = useState(null)
  const [selectedCluster, setSelectedCluster] = useState(null)

  function handleVestigingSelect(id) {
    setSelectedVestiging(id)
    setSelectedCluster(null)
  }

  return (
    <div className="p-4 max-w-6xl mx-auto">
      <h1 className="text-xl font-bold text-navy mb-4">Beheer</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <VestigingenPanel onSelect={handleVestigingSelect} selectedId={selectedVestiging} />
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <ClustersPanel vestigingId={selectedVestiging} onSelect={setSelectedCluster} selectedId={selectedCluster} />
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <KluisjesPanel clusterId={selectedCluster} />
        </div>
      </div>
    </div>
  )
}
