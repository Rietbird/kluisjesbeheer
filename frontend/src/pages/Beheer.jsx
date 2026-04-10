import { useState, useEffect, useMemo } from 'react'
import { api } from '../api'
import { useInstellingen } from '../context/InstellingenContext'

function ConfirmButton({ onConfirm, children, className }) {
  const [confirming, setConfirming] = useState(false)
  if (confirming) {
    return (
      <span className="flex gap-2">
        <button onClick={() => { setConfirming(false); onConfirm() }}
          className="px-3 py-1.5 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600">Ja, verwijder</button>
        <button onClick={() => setConfirming(false)}
          className="px-3 py-1.5 border border-slate-300 dark:border-slate-600 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700">Nee</button>
      </span>
    )
  }
  return <button onClick={() => setConfirming(true)} className={className}>{children}</button>
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
    e.preventDefault(); setError('')
    try { await api.post('/api/vestigingen', { naam, adres }); setNaam(''); setAdres(''); load() }
    catch (err) { setError(err.message) }
  }
  async function handleUpdate(id) {
    setError('')
    try { await api.put(`/api/vestigingen/${id}`, { naam: editNaam, adres: editAdres }); setEditId(null); load() }
    catch (err) { setError(err.message) }
  }
  async function handleDelete(id) {
    setError('')
    try { await api.del(`/api/vestigingen/${id}`); if (selectedId === id) onSelect(null); load() }
    catch (err) { setError(err.message) }
  }

  return (
    <div>
      <h2 className="text-base font-bold text-navy dark:text-white mb-4">Vestigingen</h2>
      {error && <p className="text-red-500 text-sm mb-3">{error}</p>}
      <div className="space-y-2 mb-5">
        {vestigingen.map(v => (
          <div key={v.id}
            className={`border-2 rounded-xl p-3 cursor-pointer transition-all ${selectedId === v.id ? 'border-primary bg-primary-50' : 'border-slate-200 dark:border-slate-600 hover:border-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'}`}>
            {editId === v.id ? (
              <div className="space-y-2">
                <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" value={editNaam}
                  onChange={e => setEditNaam(e.target.value)} placeholder="Naam" />
                <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" value={editAdres}
                  onChange={e => setEditAdres(e.target.value)} placeholder="Adres" />
                <div className="flex gap-2 mt-2">
                  <button onClick={() => handleUpdate(v.id)}
                    className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary-600">Opslaan</button>
                  <button onClick={() => setEditId(null)}
                    className="px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700">Annuleren</button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between" onClick={() => onSelect(v.id)}>
                <div>
                  <div className="font-semibold text-base">{v.naam}</div>
                  {v.adres && <div className="text-sm text-slate-500">{v.adres}</div>}
                </div>
                <div className="flex gap-2" onClick={e => e.stopPropagation()}>
                  <button onClick={() => { setEditId(v.id); setEditNaam(v.naam); setEditAdres(v.adres || '') }}
                    className="text-slate-400 hover:text-primary p-1 rounded hover:bg-slate-100 transition-colors">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                  </button>
                  <ConfirmButton onConfirm={() => handleDelete(v.id)}
                    className="text-slate-400 hover:text-red-500 p-1 rounded hover:bg-slate-100 transition-colors">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </ConfirmButton>
                </div>
              </div>
            )}
          </div>
        ))}
        {vestigingen.length === 0 && <p className="text-sm text-slate-400">Nog geen vestigingen.</p>}
      </div>
      <form onSubmit={handleAdd} className="space-y-2 border-t border-slate-200 pt-4">
        <div className="text-sm font-semibold text-slate-600 dark:text-slate-300 mb-1">Nieuwe vestiging</div>
        <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" placeholder="Naam" value={naam}
          onChange={e => setNaam(e.target.value)} required />
        <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" placeholder="Adres (optioneel)" value={adres}
          onChange={e => setAdres(e.target.value)} />
        <button type="submit"
          className="w-full bg-primary text-white rounded-lg py-2.5 text-sm font-semibold hover:bg-primary-600 transition-colors">
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
    e.preventDefault(); setError('')
    try { await api.post('/api/clusters', { vestiging_id: vestigingId, naam, standaard_borg: borg ? Number(borg) : null }); setNaam(''); setBorg(''); load() }
    catch (err) { setError(err.message) }
  }
  async function handleUpdate(id) {
    setError('')
    try { await api.put(`/api/clusters/${id}`, { naam: editNaam, standaard_borg: editBorg ? Number(editBorg) : null }); setEditId(null); load() }
    catch (err) { setError(err.message) }
  }
  async function handleDelete(id) {
    setError('')
    try { await api.del(`/api/clusters/${id}`); if (selectedId === id) onSelect(null); load() }
    catch (err) { setError(err.message) }
  }

  if (!vestigingId) return (
    <div>
      <h2 className="text-base font-bold text-navy dark:text-white mb-4">Clusters</h2>
      <p className="text-sm text-slate-400">Selecteer een vestiging.</p>
    </div>
  )

  return (
    <div>
      <h2 className="text-base font-bold text-navy dark:text-white mb-4">Clusters</h2>
      {error && <p className="text-red-500 text-sm mb-3">{error}</p>}
      <div className="space-y-2 mb-5">
        {clusters.map(c => (
          <div key={c.id}
            className={`border-2 rounded-xl p-3 cursor-pointer transition-all ${selectedId === c.id ? 'border-primary bg-primary-50' : 'border-slate-200 dark:border-slate-600 hover:border-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'}`}>
            {editId === c.id ? (
              <div className="space-y-2">
                <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" value={editNaam}
                  onChange={e => setEditNaam(e.target.value)} placeholder="Naam" />
                <input type="number" step="0.01" className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" value={editBorg}
                  onChange={e => setEditBorg(e.target.value)} placeholder="Standaard borg (€)" />
                <div className="flex gap-2 mt-2">
                  <button onClick={() => handleUpdate(c.id)}
                    className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary-600">Opslaan</button>
                  <button onClick={() => setEditId(null)}
                    className="px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700">Annuleren</button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between" onClick={() => onSelect(c.id)}>
                <div>
                  <div className="font-semibold text-base">{c.naam}</div>
                  {c.standaard_borg != null && <div className="text-sm text-slate-500">Borg: €{Number(c.standaard_borg).toFixed(2)}</div>}
                </div>
                <div className="flex gap-2" onClick={e => e.stopPropagation()}>
                  <button onClick={() => { setEditId(c.id); setEditNaam(c.naam); setEditBorg(c.standaard_borg ?? '') }}
                    className="text-slate-400 hover:text-primary p-1 rounded hover:bg-slate-100 transition-colors">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                  </button>
                  <ConfirmButton onConfirm={() => handleDelete(c.id)}
                    className="text-slate-400 hover:text-red-500 p-1 rounded hover:bg-slate-100 transition-colors">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </ConfirmButton>
                </div>
              </div>
            )}
          </div>
        ))}
        {clusters.length === 0 && <p className="text-sm text-slate-400">Nog geen clusters voor deze vestiging.</p>}
      </div>
      <form onSubmit={handleAdd} className="space-y-2 border-t border-slate-200 pt-4">
        <div className="text-sm font-semibold text-slate-600 dark:text-slate-300 mb-1">Nieuw cluster</div>
        <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" placeholder="Naam" value={naam}
          onChange={e => setNaam(e.target.value)} required />
        <input type="number" step="0.01" className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white"
          placeholder="Standaard borg (€)" value={borg} onChange={e => setBorg(e.target.value)} />
        <button type="submit"
          className="w-full bg-primary text-white rounded-lg py-2.5 text-sm font-semibold hover:bg-primary-600 transition-colors">
          + Toevoegen
        </button>
      </form>
    </div>
  )
}

// ── Kluisjes ─────────────────────────────────────────────────────────────────

function genereerReeks(prefix, van, tot, padding) {
  const items = []
  for (let i = van; i <= tot; i++) {
    const nr = padding > 0 ? String(i).padStart(padding, '0') : String(i)
    items.push(prefix + nr)
  }
  return items
}

function KluisjesPanel({ clusterId }) {
  const [kluisjes, setKluisjes] = useState([])
  const [kluisnummer, setKluisnummer] = useState('')
  const [sleutelnummer, setSleutelnummer] = useState('')
  const [locatie, setLocatie] = useState('')
  const [editId, setEditId] = useState(null)
  const [editData, setEditData] = useState({})
  const [error, setError] = useState('')
  const [addMode, setAddMode] = useState('enkel') // 'enkel' | 'bulk'
  const [selectMode, setSelectMode] = useState(false)
  const [selected, setSelected] = useState(new Set())
  // Bulk aanmaken state
  const [bulkPrefix, setBulkPrefix] = useState('')
  const [bulkVan, setBulkVan] = useState('')
  const [bulkTot, setBulkTot] = useState('')
  const [bulkPadding, setBulkPadding] = useState('3')
  const [bulkLocatie, setBulkLocatie] = useState('')
  const [bulkMsg, setBulkMsg] = useState('')

  function load() {
    if (!clusterId) { setKluisjes([]); return }
    api.get(`/api/clusters/${clusterId}/kluisjes`).then(setKluisjes).catch(() => {})
  }
  useEffect(() => { load(); setSelected(new Set()); setSelectMode(false) }, [clusterId])

  async function handleAdd(e) {
    e.preventDefault(); setError('')
    try { await api.post(`/api/clusters/${clusterId}/kluisjes`, { kluisnummer, sleutelnummer, locatie }); setKluisnummer(''); setSleutelnummer(''); setLocatie(''); load() }
    catch (err) { setError(err.message) }
  }
  async function handleUpdate(id) {
    setError('')
    try { await api.put(`/api/kluisjes/${id}`, { sleutelnummer: editData.sleutelnummer, locatie: editData.locatie }); setEditId(null); load() }
    catch (err) { setError(err.message) }
  }
  async function handleDelete(id) {
    setError('')
    try { await api.del(`/api/kluisjes/${id}`); load() }
    catch (err) { setError(err.message) }
  }

  async function handleBulkAdd(e) {
    e.preventDefault(); setError(''); setBulkMsg('')
    const van = parseInt(bulkVan)
    const tot = parseInt(bulkTot)
    if (isNaN(van) || isNaN(tot) || van > tot) { setError('Ongeldige reeks.'); return }
    if (tot - van > 499) { setError('Maximaal 500 kluisjes per keer.'); return }
    const nummers = genereerReeks(bulkPrefix, van, tot, parseInt(bulkPadding) || 0)
    const payload = nummers.map(nr => ({ kluisnummer: nr, locatie: bulkLocatie }))
    try {
      const res = await api.post(`/api/clusters/${clusterId}/kluisjes/bulk`, { kluisjes: payload })
      setBulkMsg(`${res.created} kluisjes aangemaakt${res.skipped?.length ? `, ${res.skipped.length} overgeslagen (al bestaan)` : ''}.`)
      load()
    } catch (err) { setError(err.message) }
  }

  async function handleBulkDelete() {
    if (selected.size === 0) return
    setError('')
    try {
      const res = await api.post('/api/kluisjes/bulk-verwijderen', { kluisje_ids: [...selected] })
      const msg = `${res.deleted} verwijderd${res.skipped?.length ? `, ${res.skipped.length} overgeslagen (actieve toewijzing)` : ''}.`
      setError('')
      setBulkMsg(msg)
      setSelected(new Set())
      setSelectMode(false)
      load()
    } catch (err) { setError(err.message) }
  }

  function toggleSelect(id) {
    setSelected(s => {
      const n = new Set(s)
      n.has(id) ? n.delete(id) : n.add(id)
      return n
    })
  }
  function toggleAll() {
    const vrije = kluisjes.filter(k => k.status !== 'uitgeleend').map(k => k.id)
    setSelected(s => s.size === vrije.length ? new Set() : new Set(vrije))
  }

  // Reeks preview
  const previewNummers = useMemo(() => {
    const van = parseInt(bulkVan), tot = parseInt(bulkTot)
    if (isNaN(van) || isNaN(tot) || van > tot || tot - van > 499) return []
    return genereerReeks(bulkPrefix, van, tot, parseInt(bulkPadding) || 0)
  }, [bulkPrefix, bulkVan, bulkTot, bulkPadding])

  const inputCls = "w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white"

  if (!clusterId) return (
    <div>
      <h2 className="text-base font-bold text-navy dark:text-white mb-4">Kluisjes</h2>
      <p className="text-sm text-slate-400">Selecteer een cluster.</p>
    </div>
  )

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-bold text-navy dark:text-white">Kluisjes</h2>
        <button
          onClick={() => { setSelectMode(s => !s); setSelected(new Set()); setBulkMsg('') }}
          className={`text-xs px-2.5 py-1 rounded-lg border transition-colors ${selectMode ? 'bg-red-50 border-red-300 text-red-600 dark:bg-red-900/30 dark:border-red-700 dark:text-red-400' : 'border-slate-300 dark:border-slate-600 text-slate-500 hover:border-slate-400'}`}>
          {selectMode ? 'Annuleer selectie' : 'Selecteer voor verwijderen'}
        </button>
      </div>

      {error && <p className="text-red-500 text-sm mb-3">{error}</p>}
      {bulkMsg && <p className="text-emerald-600 dark:text-emerald-400 text-sm mb-3">{bulkMsg}</p>}

      {/* Selectie toolbar */}
      {selectMode && (
        <div className="flex items-center justify-between bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl px-3 py-2 mb-3 text-sm">
          <button onClick={toggleAll} className="text-slate-500 dark:text-slate-400 hover:text-primary transition-colors">
            {selected.size === kluisjes.filter(k => k.status !== 'uitgeleend').length ? 'Deselecteer alles' : 'Selecteer alle vrije'}
          </button>
          <span className="text-slate-400">{selected.size} geselecteerd</span>
          <ConfirmButton onConfirm={handleBulkDelete}
            className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${selected.size > 0 ? 'bg-red-500 text-white hover:bg-red-600' : 'bg-slate-200 text-slate-400 cursor-not-allowed'}`}>
            Verwijder {selected.size > 0 ? `(${selected.size})` : ''}
          </ConfirmButton>
        </div>
      )}

      <div className="space-y-1.5 mb-5 max-h-80 overflow-y-auto">
        {kluisjes.map(k => (
          <div key={k.id}
            className={`border rounded-xl p-3 transition-colors ${selectMode && k.status !== 'uitgeleend' ? 'cursor-pointer' : ''} ${selected.has(k.id) ? 'border-red-300 bg-red-50 dark:border-red-700 dark:bg-red-900/20' : 'border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700'}`}
            onClick={() => selectMode && k.status !== 'uitgeleend' && toggleSelect(k.id)}>
            {!selectMode && editId === k.id ? (
              <div className="space-y-2">
                <div className="text-sm font-semibold text-navy dark:text-white">Kluisje {k.kluisnummer}</div>
                <input className={inputCls} value={editData.sleutelnummer || ''}
                  onChange={e => setEditData(d => ({ ...d, sleutelnummer: e.target.value }))} placeholder="Sleutelnr" />
                <input className={inputCls} value={editData.locatie || ''}
                  onChange={e => setEditData(d => ({ ...d, locatie: e.target.value }))} placeholder="Locatie" />
                <div className="flex gap-2 mt-2">
                  <button onClick={() => handleUpdate(k.id)}
                    className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary-600">Opslaan</button>
                  <button onClick={() => setEditId(null)}
                    className="px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700">Annuleren</button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 flex-wrap">
                  {selectMode && k.status !== 'uitgeleend' && (
                    <input type="checkbox" readOnly checked={selected.has(k.id)}
                      className="w-4 h-4 accent-red-500 pointer-events-none" />
                  )}
                  <span className="font-semibold text-navy dark:text-white">{k.kluisnummer}</span>
                  {k.sleutelnummer && <span className="text-sm text-slate-500">sleutel {k.sleutelnummer}</span>}
                  <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                    k.status === 'uitgeleend' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300' :
                    k.status === 'defect' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300' :
                    'bg-sky-100 text-sky-700 dark:bg-sky-900/50 dark:text-sky-300'
                  }`}>{k.status}</span>
                </div>
                {!selectMode && (
                  <div className="flex gap-2" onClick={e => e.stopPropagation()}>
                    <button onClick={() => { setEditId(k.id); setEditData({ sleutelnummer: k.sleutelnummer || '', locatie: k.locatie || '' }) }}
                      className="text-slate-400 hover:text-primary p-1 rounded hover:bg-slate-100 transition-colors">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                    </button>
                    <ConfirmButton onConfirm={() => handleDelete(k.id)}
                      className="text-slate-400 hover:text-red-500 p-1 rounded hover:bg-slate-100 transition-colors">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                    </ConfirmButton>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        {kluisjes.length === 0 && <p className="text-sm text-slate-400">Nog geen kluisjes in dit cluster.</p>}
      </div>

      {/* Toevoegen tabs */}
      {!selectMode && (
        <div className="border-t border-slate-200 dark:border-slate-700 pt-4">
          <div className="flex gap-1 mb-3">
            {['enkel', 'bulk'].map(m => (
              <button key={m} onClick={() => { setAddMode(m); setError(''); setBulkMsg('') }}
                className={`px-3 py-1 text-xs rounded-lg font-medium transition-colors ${addMode === m ? 'bg-primary text-white' : 'border border-slate-300 dark:border-slate-600 text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-700'}`}>
                {m === 'enkel' ? 'Eén kluisje' : 'Reeks toevoegen'}
              </button>
            ))}
          </div>

          {addMode === 'enkel' && (
            <form onSubmit={handleAdd} className="space-y-2">
              <input className={inputCls} placeholder="Kluisnummer" value={kluisnummer}
                onChange={e => setKluisnummer(e.target.value)} required />
              <input className={inputCls} placeholder="Sleutelnummer (optioneel)"
                value={sleutelnummer} onChange={e => setSleutelnummer(e.target.value)} />
              <input className={inputCls} placeholder="Locatie (optioneel)"
                value={locatie} onChange={e => setLocatie(e.target.value)} />
              <button type="submit"
                className="w-full bg-primary text-white rounded-lg py-2.5 text-sm font-semibold hover:bg-primary-600 transition-colors">
                + Toevoegen
              </button>
            </form>
          )}

          {addMode === 'bulk' && (
            <form onSubmit={handleBulkAdd} className="space-y-3">
              <p className="text-xs text-slate-500 dark:text-slate-400">Genereer een reeks kluisnummers: prefix + oplopend getal. Bijv. prefix "P", van 1 tot 50 met 3 cijfers → P001 t/m P050.</p>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs text-slate-500 mb-1">Prefix (optioneel)</label>
                  <input className={inputCls} placeholder="bijv. P of N" value={bulkPrefix}
                    onChange={e => setBulkPrefix(e.target.value)} />
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">Nullen (0 = geen)</label>
                  <input type="number" min="0" max="6" className={inputCls} value={bulkPadding}
                    onChange={e => setBulkPadding(e.target.value)} />
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">Van (getal)</label>
                  <input type="number" min="1" className={inputCls} value={bulkVan}
                    onChange={e => setBulkVan(e.target.value)} required />
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">Tot (getal)</label>
                  <input type="number" min="1" className={inputCls} value={bulkTot}
                    onChange={e => setBulkTot(e.target.value)} required />
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">Locatie (optioneel, zelfde voor alle)</label>
                <input className={inputCls} placeholder="bijv. Gang A" value={bulkLocatie}
                  onChange={e => setBulkLocatie(e.target.value)} />
              </div>
              {previewNummers.length > 0 && (
                <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-3 text-xs text-slate-600 dark:text-slate-300">
                  <span className="font-semibold">{previewNummers.length} kluisjes: </span>
                  {previewNummers.slice(0, 6).join(', ')}{previewNummers.length > 6 ? ` ... ${previewNummers[previewNummers.length - 1]}` : ''}
                </div>
              )}
              <button type="submit" disabled={previewNummers.length === 0}
                className="w-full bg-primary text-white rounded-lg py-2.5 text-sm font-semibold hover:bg-primary-600 disabled:opacity-40 transition-colors">
                {previewNummers.length > 0 ? `${previewNummers.length} kluisjes aanmaken` : 'Vul reeks in'}
              </button>
            </form>
          )}
        </div>
      )}
    </div>
  )
}

// ── Beheer Page ───────────────────────────────────────────────────────────────

function MagisterSyncPanel() {
  const [syncing, setSyncing] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  async function handleSync() {
    setSyncing(true); setError(''); setResult(null)
    try {
      const res = await api.post('/api/magister/sync-leerlingen', {})
      setResult(res)
    } catch (err) { setError(err.message) }
    finally { setSyncing(false) }
  }

  return (
    <div>
      <h2 className="text-base font-bold text-navy dark:text-white mb-3">Magister leerlingen</h2>
      <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
        Ververs de leerlingenlijst uit Magister zodat nieuwe leerlingen direct een kluisje
        toegewezen kunnen krijgen. Draait ook automatisch elke ochtend om 06:00.
      </p>

      <button onClick={handleSync} disabled={syncing}
        className="w-full bg-primary text-white rounded-lg py-2.5 text-sm font-semibold hover:bg-primary-600 disabled:opacity-50 transition-colors flex items-center justify-center gap-2">
        {syncing ? (
          <>
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Ophalen...
          </>
        ) : (
          <>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Leerlingen ophalen uit Magister
          </>
        )}
      </button>

      {error && <p className="text-red-500 text-sm mt-3">{error}</p>}
      {result && (
        <div className="mt-3 bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-700 rounded-xl p-3 text-sm">
          <div className="font-semibold text-emerald-800 dark:text-emerald-300">Leerlingen bijgewerkt</div>
          <div className="text-emerald-700 dark:text-emerald-400 mt-0.5">
            {result.leerlingen} leerlingen opgehaald, {result.klassen} klassen
          </div>
        </div>
      )}
    </div>
  )
}

// ── Kleuren Tab ───────────────────────────────────────────────────────────────

const KLEURENPALET = [
  '#14b8a6', '#0ea5e9', '#3b82f6', '#6366f1', '#8b5cf6',
  '#ec4899', '#ef4444', '#f97316', '#FF8200', '#eab308',
  '#22c55e', '#10b981', '#64748b', '#1e293b',
]

function KleurenTab() {
  const { kleurVoor, setKleurVoor, kleurMap } = useInstellingen()
  const [vestigingen, setVestigingen] = useState([])

  useEffect(() => {
    api.get('/api/vestigingen').then(setVestigingen).catch(() => {})
  }, [])

  const cardClass = "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5"

  return (
    <div className="space-y-4 max-w-2xl">
      {vestigingen.map((v, i) => {
        const huidigeKleur = kleurVoor(v.id, i)
        return (
          <div key={v.id} className={cardClass}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center text-white font-bold text-base"
                style={{ backgroundColor: huidigeKleur }}>
                {v.naam[0]}
              </div>
              <div className="font-bold text-slate-800 dark:text-white">{v.naam}</div>
            </div>
            <div className="flex flex-wrap gap-2">
              {KLEURENPALET.map(kleur => (
                <button
                  key={kleur}
                  onClick={() => setKleurVoor(v.id, kleur)}
                  title={kleur}
                  className={`w-8 h-8 rounded-lg transition-all hover:scale-110 ${huidigeKleur === kleur ? 'ring-2 ring-offset-2 ring-slate-400 scale-110' : ''}`}
                  style={{ backgroundColor: kleur }}
                />
              ))}
            </div>
          </div>
        )
      })}
      {vestigingen.length === 0 && <p className="text-sm text-slate-400">Laden...</p>}
    </div>
  )
}

// ── Borg Tab ──────────────────────────────────────────────────────────────────

function BorgTab() {
  const { borgActiefVoor, setBorgActiefVoor } = useInstellingen()
  const [vestigingen, setVestigingen] = useState([])
  const [clusters, setClusters] = useState({})
  const [editId, setEditId] = useState(null)
  const [editBorg, setEditBorg] = useState('')
  const [saving, setSaving] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.get('/api/vestigingen').then(async (vList) => {
      setVestigingen(vList)
      const map = {}
      await Promise.all(vList.map(async v => {
        const c = await api.get(`/api/vestigingen/${v.id}/clusters`)
        map[v.id] = c
      }))
      setClusters(map)
    }).catch(() => {})
  }, [])

  async function handleToggle(vestigingId) {
    setSaving(vestigingId)
    try { await setBorgActiefVoor(vestigingId, !borgActiefVoor(vestigingId)) }
    finally { setSaving(null) }
  }

  async function handleSaveBorg(clusterId) {
    setError(null)
    try {
      await api.put(`/api/clusters/${clusterId}`, {
        standaard_borg: editBorg !== '' ? Number(editBorg) : null
      })
      const vList = await api.get('/api/vestigingen')
      const map = {}
      await Promise.all(vList.map(async v => {
        const c = await api.get(`/api/vestigingen/${v.id}/clusters`)
        map[v.id] = c
      }))
      setClusters(map)
      setEditId(null)
    } catch (err) {
      setError('Borg opslaan mislukt: ' + (err?.message || 'onbekende fout'))
    }
  }

  const cardClass = "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5"
  const inputClass = "border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-1.5 text-sm bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-primary/30 focus:border-primary outline-none w-32"

  return (
    <div className="space-y-5 max-w-2xl">
      {error && (
        <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 rounded-xl px-4 py-3 text-sm">
          {error}
        </div>
      )}
      {vestigingen.map(v => (
        <div key={v.id} className={cardClass}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="font-bold text-slate-800 dark:text-white">{v.naam}</div>
              <div className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                {borgActiefVoor(v.id) ? 'Borg is ingeschakeld' : 'Borg is uitgeschakeld'}
              </div>
            </div>
            <button
              onClick={() => handleToggle(v.id)}
              disabled={saving === v.id}
              className={`flex items-center w-14 h-7 rounded-full px-0.5 transition-colors focus:outline-none ${borgActiefVoor(v.id) ? 'bg-primary' : 'bg-slate-300 dark:bg-slate-600'}`}
            >
              <span className={`w-6 h-6 rounded-full bg-white shadow-md transition-all duration-200 ${borgActiefVoor(v.id) ? 'translate-x-7' : 'translate-x-0'}`} />
            </button>
          </div>

          {borgActiefVoor(v.id) && (clusters[v.id] || []).length > 0 && (
            <div className="border-t border-slate-100 dark:border-slate-700 pt-3">
              <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-wider">Standaard borgbedragen</div>
              <div className="space-y-1">
                {(clusters[v.id] || []).map(c => (
                  <div key={c.id} className="flex items-center justify-between border border-slate-100 dark:border-slate-700 rounded-xl px-4 py-2">
                    <span className="text-sm text-slate-700 dark:text-slate-200">{c.naam}</span>
                    {editId === c.id ? (
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-slate-500">€</span>
                        <input
                          type="number" step="0.01" min="0"
                          className={inputClass}
                          value={editBorg}
                          onChange={e => setEditBorg(e.target.value)}
                          autoFocus
                        />
                        <button onClick={() => handleSaveBorg(c.id)}
                          className="px-3 py-1.5 bg-primary text-white rounded-lg text-sm hover:bg-primary-600">Opslaan</button>
                        <button onClick={() => setEditId(null)}
                          className="px-3 py-1.5 border border-slate-300 dark:border-slate-600 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700">Annuleren</button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-3">
                        <span className="text-sm text-slate-500">
                          {c.standaard_borg != null ? `€${Number(c.standaard_borg).toFixed(2)}` : '—'}
                        </span>
                        <button onClick={() => { setEditId(c.id); setEditBorg(c.standaard_borg ?? '') }}
                          className="text-slate-400 hover:text-primary p-1 rounded hover:bg-slate-100 transition-colors">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                          </svg>
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
      {vestigingen.length === 0 && <p className="text-sm text-slate-400">Laden...</p>}
    </div>
  )
}

// ── Import Tab ────────────────────────────────────────────────────────────────

function ImportTab() {
  const [vestigingen, setVestigingen] = useState([])
  const [clusters, setClusters] = useState([])
  const [importVestiging, setImportVestiging] = useState('')
  const [importCluster, setImportCluster] = useState('')
  const [importFile, setImportFile] = useState(null)
  const [importing, setImporting] = useState(false)
  const [importMsg, setImportMsg] = useState('')
  const [importError, setImportError] = useState('')

  useEffect(() => {
    api.get('/api/vestigingen').then(setVestigingen).catch(() => {})
  }, [])

  useEffect(() => {
    if (importVestiging) {
      api.get(`/api/vestigingen/${importVestiging}/clusters`).then(setClusters).catch(() => {})
    } else { setClusters([]) }
    setImportCluster('')
  }, [importVestiging])

  async function handleImport(e) {
    e.preventDefault()
    if (!importCluster || !importFile) { setImportError('Kies een cluster en een bestand.'); return }
    setImporting(true); setImportMsg(''); setImportError('')
    try {
      const formData = new FormData()
      formData.append('cluster_id', importCluster)
      formData.append('file', importFile)
      const res = await api.upload('/api/kluisjes/import', formData)
      const fmt = res.format === 'mx' ? 'Magister MX' : res.format === 'desktop' ? 'Magister Desktop' : 'standaard'
      let msg = `Import geslaagd (${fmt}): ${res.imported} kluisjes aangemaakt`
      if (res.toewijzingen > 0) msg += `, ${res.toewijzingen} toewijzingen`
      if (res.skipped > 0) msg += `, ${res.skipped} overgeslagen (al bestaand)`
      setImportMsg(msg + '.')
      setImportFile(null)
      const fileInput = document.getElementById('xlsx-file-input-beheer')
      if (fileInput) fileInput.value = ''
    } catch (err) { setImportError(`Import mislukt: ${err.message}`) }
    finally { setImporting(false) }
  }

  const selectClass = "w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2.5 text-sm bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-primary/30 focus:border-primary outline-none"
  const btnClass = "bg-primary text-white rounded-lg px-5 py-2.5 text-sm font-semibold hover:bg-primary-600 disabled:opacity-50 transition-colors"
  const cardClass = "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6"

  return (
    <div className="max-w-2xl">
      <div className={cardClass}>
        <h2 className="text-base font-bold text-slate-800 dark:text-white mb-2">Import kluisjes</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
          Importeer kluisjes vanuit een Magister Excel-export (.xlsx). Zowel Magister MX als Desktop formaat wordt automatisch herkend. Kluisjes die al uitgeleend zijn worden inclusief toewijzing geïmporteerd.
        </p>
        <form onSubmit={handleImport} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1.5 font-medium">Vestiging</label>
            <select className={selectClass} value={importVestiging} onChange={e => setImportVestiging(e.target.value)}>
              <option value="">Kies vestiging...</option>
              {vestigingen.map(v => <option key={v.id} value={v.id}>{v.naam}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1.5 font-medium">Cluster</label>
            <select className={selectClass} value={importCluster} onChange={e => setImportCluster(e.target.value)} disabled={!importVestiging}>
              <option value="">Kies cluster...</option>
              {clusters.map(c => <option key={c.id} value={c.id}>{c.naam}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1.5 font-medium">Excel-bestand (.xlsx)</label>
            <input id="xlsx-file-input-beheer" type="file" accept=".xlsx"
              className="w-full text-sm text-slate-600 dark:text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-50 dark:file:bg-primary-700 file:text-primary-700 dark:file:text-white hover:file:bg-primary-100"
              onChange={e => setImportFile(e.target.files[0] || null)} />
          </div>

          <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4">
            <div className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Ondersteunde formaten</div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">Het formaat wordt automatisch herkend aan de kolomnamen.</p>
            <div className="space-y-3">
              <div>
                <div className="text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Magister MX</div>
                <div className="text-xs text-slate-500 dark:text-slate-400 font-mono bg-white dark:bg-slate-800 rounded px-2 py-1.5 border border-slate-200 dark:border-slate-600">
                  Cluster | Kluis | Naam | Stamnummer | Klas | Uitleenperiode | Status | Borgbedrag | Locatie | Sleutel
                </div>
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Magister Desktop</div>
                <div className="text-xs text-slate-500 dark:text-slate-400 font-mono bg-white dark:bg-slate-800 rounded px-2 py-1.5 border border-slate-200 dark:border-slate-600">
                  Stamnr | Omschrijving Kluisje | Slotnummer | Achternaam | Tussenv | Roepnaam | Verhuur vanaf | Verhuur tot/met
                </div>
              </div>
            </div>
          </div>

          {importError && <p className="text-red-500 text-sm">{importError}</p>}
          {importMsg && <p className="text-emerald-600 text-sm font-medium">{importMsg}</p>}
          <button type="submit" disabled={importing} className={btnClass}>
            {importing ? 'Importeren...' : 'Importeren'}
          </button>
        </form>
      </div>

      {/* Magister sync */}
      <div className={cardClass} style={{ marginTop: '1.25rem' }}>
        <MagisterSyncPanel />
      </div>
    </div>
  )
}

// ── Instellingen Tab ──────────────────────────────────────────────────────────

function BeheerInstellingenTab() {
  const [periodeVan, setPeriodeVan] = useState('')
  const [periodeTot, setPeriodeTot] = useState('')
  const [regio, setRegio] = useState('noord')
  const [schoolNaam, setSchoolNaam] = useState('')
  const [schoolSubtitel, setSchoolSubtitel] = useState('')
  const [schoolKleur, setSchoolKleur] = useState('#FF8200')
  const [logoFile, setLogoFile] = useState(null)
  const [logoPreview, setLogoPreview] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState('')
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    api.get('/api/instellingen')
      .then(data => {
        setPeriodeVan(data.standaard_periode_van || '')
        setPeriodeTot(data.standaard_periode_tot || '')
        setRegio(data.regio || 'noord')
        setSchoolNaam(data.schoolNaam || '')
        setSchoolSubtitel(data.schoolSubtitel || '')
        setSchoolKleur(data.schoolKleur || '#FF8200')
        if (data.schoolLogo) setLogoPreview(data.schoolLogo)
        // Fallback: load from branding API if not in instellingen
        if (!data.schoolLogo || !data.schoolNaam) {
          api.get('/api/branding').then(b => {
            if (!data.schoolNaam && b.schoolNaam) setSchoolNaam(b.schoolNaam)
            if (!data.schoolSubtitel && b.schoolSubtitel) setSchoolSubtitel(b.schoolSubtitel)
            if (!data.schoolKleur && b.schoolKleur) setSchoolKleur(b.schoolKleur)
            if (!data.schoolLogo && b.schoolLogo) setLogoPreview(b.schoolLogo)
          }).catch(() => {})
        }
      })
      .catch(() => {})
      .finally(() => setLoaded(true))
  }, [])

  async function handleSavePeriode(e) {
    e.preventDefault(); setSaving(true); setSaveMsg('')
    try {
      await api.put('/api/instellingen', {
        standaard_periode_van: periodeVan,
        standaard_periode_tot: periodeTot,
        regio,
      })
      setSaveMsg('Opgeslagen!')
      setTimeout(() => setSaveMsg(''), 2000)
    } catch (err) { setSaveMsg(`Fout: ${err.message}`) }
    finally { setSaving(false) }
  }

  async function handleSaveBranding() {
    setSaving(true); setSaveMsg('')
    try {
      await api.put('/api/instellingen', {
        schoolNaam,
        schoolSubtitel,
        schoolKleur,
      })
      if (logoFile) {
        const formData = new FormData()
        formData.append('file', logoFile)
        const res = await api.upload('/api/instellingen/logo', formData)
        setLogoPreview(res.schoolLogo)
        setLogoFile(null)
      }
      setSaveMsg('Opgeslagen! Ververs de pagina om de wijzigingen te zien.')
      setTimeout(() => setSaveMsg(''), 5000)
    } catch (err) { setSaveMsg(`Fout: ${err.message}`) }
    finally { setSaving(false) }
  }

  const inputClass = "w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2.5 text-sm bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-primary/30 focus:border-primary outline-none transition-all"
  const btnClass = "bg-primary text-white rounded-lg px-5 py-2.5 text-sm font-semibold hover:bg-primary-600 disabled:opacity-50 transition-colors"
  const cardClass = "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6"

  if (!loaded) return <div className="p-4 text-sm text-slate-400">Laden...</div>

  return (
    <div className="max-w-2xl space-y-5">
      <div className={cardClass}>
        <h2 className="text-base font-bold text-slate-800 dark:text-white mb-4">Standaard uitleenperiode</h2>
        <form onSubmit={handleSavePeriode} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1.5 font-medium">Van (MM-DD)</label>
              <input className={inputClass} placeholder="09-01" value={periodeVan}
                onChange={e => setPeriodeVan(e.target.value)} pattern="\d{2}-\d{2}" />
            </div>
            <div>
              <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1.5 font-medium">Tot (MM-DD)</label>
              <input className={inputClass} placeholder="07-31" value={periodeTot}
                onChange={e => setPeriodeTot(e.target.value)} pattern="\d{2}-\d{2}" />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button type="submit" disabled={saving} className={btnClass}>
              {saving ? 'Opslaan...' : 'Opslaan'}
            </button>
            {saveMsg && (
              <span className={`text-sm font-medium ${saveMsg.startsWith('Fout') ? 'text-red-500' : 'text-emerald-600'}`}>
                {saveMsg}
              </span>
            )}
          </div>
        </form>
      </div>

      <div className={cardClass}>
        <h2 className="text-base font-bold text-slate-800 dark:text-white mb-2">Regio</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
          De regio bepaalt de standaard uitleenperiode op basis van de zomervakantie.
        </p>
        <select className={inputClass} value={regio} onChange={e => setRegio(e.target.value)}>
          <option value="noord">Noord</option>
          <option value="midden">Midden</option>
          <option value="zuid">Zuid</option>
        </select>
      </div>

      <div className={cardClass}>
        <h2 className="text-base font-bold text-slate-800 dark:text-white mb-4">School branding</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1.5 font-medium">Schoolnaam</label>
            <input className={inputClass} value={schoolNaam} onChange={e => setSchoolNaam(e.target.value)}
              placeholder="Naam van de school" />
          </div>
          <div>
            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1.5 font-medium">Subtitel</label>
            <input className={inputClass} value={schoolSubtitel} onChange={e => setSchoolSubtitel(e.target.value)}
              placeholder="Subtitel onder 'Kluisjesbeheer'" />
          </div>
          <div>
            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1.5 font-medium">Schoolkleur</label>
            <div className="flex items-center gap-3">
              <input type="color" value={schoolKleur} onChange={e => setSchoolKleur(e.target.value)}
                className="w-10 h-10 rounded-lg border border-slate-300 dark:border-slate-600 cursor-pointer" />
              <input className={inputClass + ' !w-32'} value={schoolKleur} onChange={e => setSchoolKleur(e.target.value)}
                placeholder="#FF8200" pattern="^#[0-9a-fA-F]{6}$" />
            </div>
          </div>
          <div>
            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1.5 font-medium">Logo</label>
            <div className="flex items-center gap-4">
              {logoPreview && <img src={logoPreview} alt="Logo" className="h-10 w-auto rounded" />}
              <input type="file" accept=".png,.jpg,.jpeg,.svg"
                className="text-sm text-slate-600 dark:text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-50 dark:file:bg-primary-700 file:text-primary-700 dark:file:text-white"
                onChange={e => setLogoFile(e.target.files[0] || null)} />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button type="button" onClick={handleSaveBranding} disabled={saving} className={btnClass}>
              {saving ? 'Opslaan...' : 'Opslaan'}
            </button>
            {saveMsg && (
              <span className={`text-sm font-medium ${saveMsg.startsWith('Fout') ? 'text-red-500' : 'text-emerald-600'}`}>
                {saveMsg}
              </span>
            )}
          </div>
        </div>
      </div>

    </div>
  )
}

// ── Locaties per vestiging Tab ────────────────────────────────────────────────

function KlassenTab() {
  const [vestigingen, setVestigingen] = useState([])
  const [alleLocaties, setAlleLocaties] = useState([])
  const [vestigingLocaties, setVestigingLocaties] = useState({}) // { vestiging_id: Set }
  const [saving, setSaving] = useState(null)
  const [msg, setMsg] = useState('')

  useEffect(() => {
    api.get('/api/vestigingen').then(async vList => {
      setVestigingen(vList)
      const locs = await api.get('/api/magister/locaties')
      setAlleLocaties(locs)
      const map = {}
      await Promise.all(vList.map(async v => {
        const vl = await api.get(`/api/vestigingen/${v.id}/locaties`)
        map[v.id] = new Set(vl)
      }))
      setVestigingLocaties(map)
    }).catch(() => {})
  }, [])

  async function handleToggle(vestigingId, locatie) {
    const prev = vestigingLocaties[vestigingId] || new Set()
    const updated = new Set(prev)
    if (updated.has(locatie)) updated.delete(locatie)
    else updated.add(locatie)
    setVestigingLocaties(m => ({ ...m, [vestigingId]: updated }))
    setSaving(vestigingId)
    try {
      await api.put(`/api/vestigingen/${vestigingId}/locaties`, { locaties: [...updated] })
      setMsg('Opgeslagen')
      setTimeout(() => setMsg(''), 2000)
    } catch {
      setVestigingLocaties(m => ({ ...m, [vestigingId]: prev }))
    } finally { setSaving(null) }
  }

  const cardClass = "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5"

  return (
    <div className="space-y-5 max-w-3xl">
      <p className="text-sm text-slate-500 dark:text-slate-400">
        Koppel Magister-locaties aan vestigingen. Bij het zoeken van een leerling worden dan alleen leerlingen van de gekoppelde locaties getoond.
      </p>
      {msg && <div className="text-sm text-emerald-600 dark:text-emerald-400">{msg}</div>}
      {vestigingen.map(v => {
        const geselecteerd = vestigingLocaties[v.id] || new Set()
        return (
          <div key={v.id} className={cardClass}>
            <div className="flex items-center justify-between mb-3">
              <div className="font-bold text-slate-800 dark:text-white">{v.naam}</div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-400">{geselecteerd.size} gekoppeld</span>
                {saving === v.id && <span className="text-xs text-slate-400">Opslaan...</span>}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {alleLocaties.map(loc => (
                <button key={loc} onClick={() => handleToggle(v.id, loc)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border ${
                    geselecteerd.has(loc)
                      ? 'bg-primary text-white border-primary'
                      : 'bg-white dark:bg-slate-700 text-slate-600 dark:text-slate-300 border-slate-300 dark:border-slate-600 hover:border-primary'
                  }`}>
                  {loc}
                </button>
              ))}
            </div>
          </div>
        )
      })}
      {vestigingen.length === 0 && <p className="text-sm text-slate-400">Laden...</p>}
    </div>
  )
}

const TABS = ['Vestigingen & Kluisjes', 'Borg', 'Kleuren', 'Locaties', 'Import', 'Instellingen']

export default function Beheer({ onClose }) {
  const [activeTab, setActiveTab] = useState(0)
  const [selectedVestiging, setSelectedVestiging] = useState(null)
  const [selectedCluster, setSelectedCluster] = useState(null)

  return (
    <div className="p-6 sm:p-8 max-w-6xl mx-auto">
      {/* Terug knop */}
      <button onClick={onClose}
        className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400 hover:text-primary dark:hover:text-primary transition-colors mb-4">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Terug naar overzicht
      </button>

      <h1 className="text-2xl font-bold text-navy dark:text-white mb-5">Beheer</h1>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-slate-200 dark:border-slate-700 mb-6">
        {TABS.map((tab, i) => (
          <button key={tab} onClick={() => setActiveTab(i)}
            className={`px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === i
                ? 'bg-white dark:bg-slate-800 border border-b-white dark:border-slate-700 dark:border-b-slate-800 text-primary -mb-px'
                : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
            }`}>
            {tab}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5">
            <VestigingenPanel onSelect={id => { setSelectedVestiging(id); setSelectedCluster(null) }} selectedId={selectedVestiging} />
          </div>
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5">
            <ClustersPanel vestigingId={selectedVestiging} onSelect={setSelectedCluster} selectedId={selectedCluster} />
          </div>
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5">
            <KluisjesPanel clusterId={selectedCluster} />
          </div>
        </div>
      )}
      {activeTab === 1 && <BorgTab />}
      {activeTab === 2 && <KleurenTab />}
      {activeTab === 3 && <KlassenTab />}
      {activeTab === 4 && <ImportTab />}
      {activeTab === 5 && <BeheerInstellingenTab />}
    </div>
  )
}
