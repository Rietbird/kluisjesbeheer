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
              <>
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
                {selectedId === v.id && (
                  <VestigingDetailPanel vestiging={v} index={vestigingen.indexOf(v)} />
                )}
              </>
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

function KluisjesPanel({ clusterId, vestigingId }) {
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
  const [clusters, setClusters] = useState([])
  const [verplaatsDoel, setVerplaatsDoel] = useState('')
  const [verplaatsPrefix, setVerplaatsPrefix] = useState('')
  const [verplaatsVan, setVerplaatsVan] = useState('')
  const [verplaatsTot, setVerplaatsTot] = useState('')

  function load() {
    if (!clusterId) { setKluisjes([]); return }
    api.get(`/api/clusters/${clusterId}/kluisjes`).then(setKluisjes).catch(() => {})
  }
  useEffect(() => { load(); setSelected(new Set()); setSelectMode(false) }, [clusterId])

  useEffect(() => {
    if (!vestigingId) { setClusters([]); return }
    api.get(`/api/vestigingen/${vestigingId}/clusters`).then(setClusters).catch(() => {})
  }, [vestigingId, clusterId])

  async function handleVerplaatsReeks() {
    if (!verplaatsDoel) { setError('Kies een doelcluster.'); return }
    setError(''); setBulkMsg('')
    const van = parseInt(verplaatsVan), tot = parseInt(verplaatsTot)
    if (isNaN(van) || isNaN(tot) || van > tot) { setError('Ongeldige reeks.'); return }
    try {
      const res = await api.post(`/api/clusters/${verplaatsDoel}/verplaats-reeks`,
        { prefix: verplaatsPrefix, van, tot })
      setBulkMsg(`${res.verplaatst} kluisjes verplaatst.`)
      load()
    } catch (err) { setError(err.message) }
  }

  async function handleVerplaatsSelectie() {
    if (!verplaatsDoel) { setError('Kies een doelcluster.'); return }
    if (selected.size === 0) return
    setError(''); setBulkMsg('')
    try {
      const res = await api.post(`/api/clusters/${verplaatsDoel}/verplaats-selectie`,
        { kluisje_ids: [...selected] })
      setBulkMsg(`${res.verplaatst} kluisjes verplaatst.`)
      setSelected(new Set()); setSelectMode(false)
      load()
    } catch (err) { setError(err.message) }
  }

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
        <div className="bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl px-3 py-2 mb-3 text-sm space-y-2">
          <div className="flex items-center justify-between">
            <button onClick={toggleAll} className="text-slate-500 dark:text-slate-400 hover:text-primary transition-colors">
              {selected.size === kluisjes.filter(k => k.status !== 'uitgeleend').length ? 'Deselecteer alles' : 'Selecteer alle vrije'}
            </button>
            <span className="text-slate-400">{selected.size} geselecteerd</span>
            <ConfirmButton onConfirm={handleBulkDelete}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${selected.size > 0 ? 'bg-red-500 text-white hover:bg-red-600' : 'bg-slate-200 text-slate-400 cursor-not-allowed'}`}>
              Verwijder {selected.size > 0 ? `(${selected.size})` : ''}
            </ConfirmButton>
          </div>
          {clusters.length > 1 && (
            <div className="flex items-center gap-2 pt-2 border-t border-slate-200 dark:border-slate-600">
              <select value={verplaatsDoel} onChange={e => setVerplaatsDoel(e.target.value)}
                className="flex-1 border border-slate-300 dark:border-slate-600 rounded-lg px-2 py-1 text-sm dark:bg-slate-700 dark:text-white">
                <option value="">— verplaats naar cluster —</option>
                {clusters.filter(c => String(c.id) !== String(clusterId)).map(c => (
                  <option key={c.id} value={c.id}>{c.naam}</option>
                ))}
              </select>
              <button onClick={handleVerplaatsSelectie}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${selected.size > 0 && verplaatsDoel ? 'bg-primary text-white hover:bg-primary-600' : 'bg-slate-200 text-slate-400 cursor-not-allowed'}`}>
                Verplaats {selected.size > 0 ? `(${selected.size})` : ''}
              </button>
            </div>
          )}
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
                    k.status === 'uitgeleend' ? 'bg-sky-100 text-sky-700 dark:bg-sky-900/50 dark:text-sky-300' :
                    'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300'
                  }`}>{k.status}</span>
                  {!!k.is_defect && (
                    <span className="text-xs px-2.5 py-0.5 rounded-full font-medium bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300">defect</span>
                  )}
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

      {/* Verplaats bestaande kluisjes naar cluster (reeks) */}
      {!selectMode && clusters.length > 1 && (
        <div className="mb-4 p-3 rounded-xl border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/40">
          <div className="text-xs font-semibold text-slate-600 dark:text-slate-300 mb-2">
            Bestaande kluisjes verplaatsen naar cluster
          </div>
          <select value={verplaatsDoel} onChange={e => setVerplaatsDoel(e.target.value)}
            className={inputCls + ' mb-2'}>
            <option value="">— kies doelcluster —</option>
            {clusters.filter(c => String(c.id) !== String(clusterId)).map(c => (
              <option key={c.id} value={c.id}>{c.naam}</option>
            ))}
          </select>
          <div className="grid grid-cols-3 gap-2 mb-2">
            <input className={inputCls} placeholder="prefix (bv. MO-)"
              value={verplaatsPrefix} onChange={e => setVerplaatsPrefix(e.target.value)} />
            <input className={inputCls} placeholder="van" inputMode="numeric"
              value={verplaatsVan} onChange={e => setVerplaatsVan(e.target.value)} />
            <input className={inputCls} placeholder="tot" inputMode="numeric"
              value={verplaatsTot} onChange={e => setVerplaatsTot(e.target.value)} />
          </div>
          <button onClick={handleVerplaatsReeks}
            className="w-full px-3 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary-600 transition-colors">
            Verplaats reeks
          </button>
        </div>
      )}

      {/* Toevoegen tabs */}
      {!selectMode && (
        <div className="border-t border-slate-200 dark:border-slate-700 pt-4">
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">
            Hiermee maak je <strong>nieuwe</strong> kluisjes aan in dit cluster.
            Bestaande kluisjes verplaatsen doe je hierboven met "Verplaats".
          </p>
          <div className="flex gap-1 mb-3">
            {['enkel', 'bulk'].map(m => (
              <button key={m} onClick={() => { setAddMode(m); setError(''); setBulkMsg('') }}
                className={`px-3 py-1 text-xs rounded-lg font-medium transition-colors ${addMode === m ? 'bg-primary text-white' : 'border border-slate-300 dark:border-slate-600 text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-700'}`}>
                {m === 'enkel' ? 'Eén kluisje aanmaken' : 'Reeks aanmaken'}
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
  const [configured, setConfigured] = useState(null)

  useEffect(() => {
    api.get('/api/magister/config')
      .then(data => setConfigured(data.configured))
      .catch(() => setConfigured(false))
  }, [])

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
      {configured === false && (
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl px-4 py-3 text-sm text-amber-700 dark:text-amber-300 mb-4">
          Magister API is nog niet geconfigureerd. Ga naar <strong>Instellingen</strong> om de koppeling in te stellen.
        </div>
      )}
      <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
        Ververs de leerlingenlijst uit Magister zodat nieuwe leerlingen direct een kluisje
        toegewezen kunnen krijgen. Draait ook automatisch elke ochtend om 06:00.
      </p>

      <button onClick={handleSync} disabled={syncing || configured === false}
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

// ── Kleuren palet ────────────────────────────────────────────────────────────

const KLEURENPALET = [
  '#14b8a6', '#0ea5e9', '#3b82f6', '#6366f1', '#8b5cf6',
  '#ec4899', '#ef4444', '#f97316', '#FF8200', '#eab308',
  '#22c55e', '#10b981', '#64748b', '#1e293b',
]

// ── Vestiging detail panel (kleur, borg, locaties) ──────────────────────────

function VestigingDetailPanel({ vestiging, index }) {
  const { kleurVoor, setKleurVoor, borgActiefVoor, setBorgActiefVoor } = useInstellingen()
  const [clusters, setClusters] = useState([])
  const [alleLocaties, setAlleLocaties] = useState([])
  const [vestigingLocaties, setVestigingLocaties] = useState(new Set())
  const [editBorgId, setEditBorgId] = useState(null)
  const [editBorg, setEditBorg] = useState('')
  const [saving, setSaving] = useState(null)
  const [resetMsg, setResetMsg] = useState('')

  useEffect(() => {
    api.get(`/api/vestigingen/${vestiging.id}/clusters`).then(setClusters).catch(() => {})
    api.get('/api/magister/locaties').then(setAlleLocaties).catch(() => {})
    api.get(`/api/vestigingen/${vestiging.id}/locaties`).then(locs => setVestigingLocaties(new Set(locs))).catch(() => {})
  }, [vestiging.id])

  async function handleToggleBorg() {
    setSaving('borg')
    try { await setBorgActiefVoor(vestiging.id, !borgActiefVoor(vestiging.id)) }
    finally { setSaving(null) }
  }

  async function handleSaveBorg(clusterId) {
    try {
      await api.put(`/api/clusters/${clusterId}`, { standaard_borg: editBorg !== '' ? Number(editBorg) : null })
      setClusters(await api.get(`/api/vestigingen/${vestiging.id}/clusters`))
      setEditBorgId(null)
    } catch {}
  }

  async function handleToggleLocatie(locatie) {
    const updated = new Set(vestigingLocaties)
    if (updated.has(locatie)) updated.delete(locatie); else updated.add(locatie)
    setVestigingLocaties(updated)
    try { await api.put(`/api/vestigingen/${vestiging.id}/locaties`, { locaties: [...updated] }) }
    catch { setVestigingLocaties(vestigingLocaties) }
  }

  const huidigeKleur = kleurVoor(vestiging.id, index)

  return (
    <div className="space-y-4 mt-3 pt-3 border-t border-slate-100 dark:border-slate-700">
      {/* Kleur */}
      <div>
        <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-wider">Kleur</div>
        <div className="flex flex-wrap gap-1.5">
          {KLEURENPALET.map(kleur => (
            <button key={kleur} onClick={() => setKleurVoor(vestiging.id, kleur)} title={kleur}
              className={`w-7 h-7 rounded-lg transition-all hover:scale-110 ${huidigeKleur === kleur ? 'ring-2 ring-offset-2 ring-slate-400 scale-110' : ''}`}
              style={{ backgroundColor: kleur }} />
          ))}
        </div>
      </div>

      {/* Borg */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Borg</div>
          <button onClick={handleToggleBorg} disabled={saving === 'borg'}
            className={`flex items-center w-12 h-6 rounded-full px-0.5 transition-colors ${borgActiefVoor(vestiging.id) ? 'bg-primary' : 'bg-slate-300 dark:bg-slate-600'}`}>
            <span className={`w-5 h-5 rounded-full bg-white shadow-md transition-all duration-200 ${borgActiefVoor(vestiging.id) ? 'translate-x-6' : 'translate-x-0'}`} />
          </button>
        </div>
        {borgActiefVoor(vestiging.id) && clusters.length > 0 && (
          <div className="space-y-1">
            {clusters.map(c => (
              <div key={c.id} className="flex items-center justify-between text-sm py-1">
                <span className="text-slate-600 dark:text-slate-300">{c.naam}</span>
                {editBorgId === c.id ? (
                  <div className="flex items-center gap-1.5">
                    <span className="text-slate-500">€</span>
                    <input type="number" step="0.01" min="0" value={editBorg} onChange={e => setEditBorg(e.target.value)}
                      className="border border-slate-300 dark:border-slate-600 rounded-lg px-2 py-1 text-sm dark:bg-slate-700 dark:text-white w-24" autoFocus />
                    <button onClick={() => handleSaveBorg(c.id)} className="px-2 py-1 bg-primary text-white rounded-lg text-xs">OK</button>
                    <button onClick={() => setEditBorgId(null)} className="px-2 py-1 text-xs text-slate-500">✕</button>
                  </div>
                ) : (
                  <button onClick={() => { setEditBorgId(c.id); setEditBorg(c.standaard_borg ?? '') }}
                    className="text-slate-500 hover:text-primary text-sm">
                    {c.standaard_borg != null ? `€${Number(c.standaard_borg).toFixed(2)}` : '— klik om in te stellen'}
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Locaties */}
      {alleLocaties.length > 0 && (
        <div>
          <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-wider">
            Magister-locaties <span className="normal-case font-normal">({vestigingLocaties.size} gekoppeld)</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {alleLocaties.map(loc => (
              <button key={loc} onClick={() => handleToggleLocatie(loc)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors border ${
                  vestigingLocaties.has(loc)
                    ? 'bg-primary text-white border-primary'
                    : 'bg-white dark:bg-slate-700 text-slate-500 dark:text-slate-300 border-slate-300 dark:border-slate-600 hover:border-primary'
                }`}>
                {loc}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Reset vestiging */}
      <div className="pt-2 border-t border-slate-100 dark:border-slate-700">
        <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-wider">Gegevens wissen</div>
        {resetMsg && <p className={`text-xs mb-2 ${resetMsg.startsWith('Fout') ? 'text-red-500' : 'text-emerald-600'}`}>{resetMsg}</p>}
        <ConfirmButton onConfirm={async () => {
          setResetMsg('')
          try {
            const res = await api.post(`/api/vestigingen/${vestiging.id}/reset`, {})
            setResetMsg(`${res.deleted_kluisjes} kluisjes en ${res.deleted_toewijzingen} toewijzingen verwijderd.`)
          } catch (err) { setResetMsg(`Fout: ${err.message}`) }
        }} className="text-xs px-3 py-1.5 rounded-lg border border-red-300 text-red-600 hover:bg-red-50 dark:border-red-700 dark:text-red-400 dark:hover:bg-red-900/20 transition-colors">
          Alle kluisjes en toewijzingen wissen
        </ConfirmButton>
        <p className="text-xs text-slate-400 mt-1">Vestiging en clusters blijven behouden.</p>
      </div>
    </div>
  )
}

// ── Import Tab ────────────────────────────────────────────────────────────────

function ImportTab() {
  const [importFile, setImportFile] = useState(null)
  const [importing, setImporting] = useState(false)
  const [importMsg, setImportMsg] = useState('')
  const [importError, setImportError] = useState('')
  const [preview, setPreview] = useState(null) // result from /import/preview
  const [prefixNames, setPrefixNames] = useState({}) // prefix -> vestigingnaam
  const [normaliseer, setNormaliseer] = useState(false)

  async function handlePreview() {
    if (!importFile) { setImportError('Kies een bestand.'); return }
    setImporting(true); setImportMsg(''); setImportError(''); setPreview(null)
    try {
      const formData = new FormData()
      formData.append('file', importFile)
      const res = await api.upload('/api/kluisjes/import/preview', formData)
      setPreview(res)
      // Default AAN bij kromme data zonder collision; UIT anders
      const n = res.normalisatie
      setNormaliseer(!!(n && n.heeft_krom && !n.heeft_collision))
      // Pre-fill prefix names: use locatie if available, otherwise prefix itself
      const names = {}
      if (res.has_locaties) {
        res.locaties.forEach(l => { names[l.locatie] = l.locatie })
      } else {
        res.prefixes.forEach(p => { names[p.prefix] = p.prefix })
      }
      setPrefixNames(names)
    } catch (err) { setImportError(`Preview mislukt: ${err.message}`) }
    finally { setImporting(false) }
  }

  async function handleImport(e) {
    e.preventDefault()
    if (!importFile) { setImportError('Kies een bestand.'); return }
    setImporting(true); setImportMsg(''); setImportError('')
    try {
      const formData = new FormData()
      formData.append('file', importFile)
      if (preview?.has_locaties) {
        formData.append('auto_vestiging', '1')
        formData.append('locatie_mapping', JSON.stringify(prefixNames))
      } else {
        formData.append('prefix_mapping', JSON.stringify(prefixNames))
      }
      formData.append('normaliseer', normaliseer ? '1' : '')
      const res = await api.upload('/api/kluisjes/import', formData)
      const fmt = res.format === 'mx' ? 'Magister MX' : res.format === 'desktop' ? 'Magister Desktop' : 'standaard'
      let msg = `Import geslaagd (${fmt}): ${res.imported} kluisjes aangemaakt`
      if (res.toewijzingen > 0) msg += `, ${res.toewijzingen} toewijzingen`
      if (res.skipped > 0) msg += `, ${res.skipped} overgeslagen (al bestaand)`
      setImportMsg(msg + '.')
      setImportFile(null); setPreview(null)
      const fileInput = document.getElementById('xlsx-file-input-beheer')
      if (fileInput) fileInput.value = ''
    } catch (err) { setImportError(`Import mislukt: ${err.message}`) }
    finally { setImporting(false) }
  }

  const inputClass = "w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-primary/30 focus:border-primary outline-none"
  const btnClass = "bg-primary text-white rounded-lg px-5 py-2.5 text-sm font-semibold hover:bg-primary-600 disabled:opacity-50 transition-colors"
  const cardClass = "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6"

  return (
    <div className="max-w-2xl">
      <div className={cardClass}>
        <h2 className="text-base font-bold text-slate-800 dark:text-white mb-2">Import kluisjes</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
          Importeer kluisjes vanuit een Magister Excel-export (.xlsx). Zowel Magister MX als Desktop formaat wordt automatisch herkend. Kluisjes die al uitgeleend zijn worden inclusief toewijzing geïmporteerd.
        </p>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1.5 font-medium">Stap 1: Excel-bestand kiezen (.xlsx)</label>
            <input id="xlsx-file-input-beheer" type="file" accept=".xlsx"
              className="w-full text-sm text-slate-600 dark:text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-50 dark:file:bg-primary-700 file:text-primary-700 dark:file:text-white hover:file:bg-primary-100"
              onChange={e => { setImportFile(e.target.files[0] || null); setPreview(null); setImportMsg(''); setImportError('') }} />
          </div>

          {!preview && (
            <button type="button" onClick={handlePreview} disabled={importing || !importFile} className={btnClass}>
              {importing ? 'Bestand analyseren...' : 'Bestand analyseren'}
            </button>
          )}

          {preview && (
            <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4 space-y-4">
              <div className="text-sm font-medium text-slate-700 dark:text-slate-300">
                Stap 2: Controleer de indeling
                <span className="ml-2 text-xs font-normal text-slate-400">
                  {preview.format === 'mx' ? 'Magister MX' : preview.format === 'desktop' ? 'Magister Desktop' : 'Standaard'} — {preview.total} kluisjes gevonden
                </span>
              </div>

              {preview.normalisatie?.heeft_krom && (
                <div className="p-3 rounded-xl border border-amber-200 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-800 text-sm">
                  {preview.normalisatie.heeft_collision ? (
                    <p className="text-amber-700 dark:text-amber-300">
                      De nummering is inconsistent, maar normaliseren is niet mogelijk:
                      sommige nummers zouden samenvallen. De import gaat ongewijzigd door.
                    </p>
                  ) : (
                    <label className="flex items-start gap-2 cursor-pointer text-slate-700 dark:text-slate-200">
                      <input type="checkbox" checked={normaliseer}
                        onChange={e => setNormaliseer(e.target.checked)}
                        className="mt-0.5 w-4 h-4 accent-primary" />
                      <span>
                        De nummering sorteert niet logisch (bv. MO-1, MO-10, MO-100…).
                        <strong> Kluisnummers normaliseren naar vaste breedte</strong>
                        {' '}(bv. MO-0001) zodat sortering overal klopt.
                      </span>
                    </label>
                  )}
                </div>
              )}

              {preview.has_locaties ? (
                <div>
                  <div className="text-xs font-semibold text-slate-600 dark:text-slate-300 mb-2">Vestigingen uit bestand — pas eventueel de naam aan</div>
                  <div className="space-y-2">
                    {preview.locaties.map(l => (
                      <div key={l.locatie} className="flex items-center gap-3">
                        <span className="text-xs text-slate-400 w-10 text-right">{l.count}x</span>
                        <span className="text-xs text-slate-500 dark:text-slate-400 flex-shrink-0 max-w-[180px] truncate" title={l.locatie}>{l.locatie}</span>
                        <span className="text-slate-400">→</span>
                        <input className={inputClass + ' flex-1'} value={prefixNames[l.locatie] || ''}
                          onChange={e => setPrefixNames(m => ({ ...m, [l.locatie]: e.target.value }))}
                          placeholder="Vestigingnaam" />
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-slate-400 mt-2">Vestigingen worden automatisch aangemaakt met de opgegeven naam.</p>
                </div>
              ) : (
                <div>
                  <div className="text-xs font-semibold text-slate-600 dark:text-slate-300 mb-2">Gevonden prefixen — geef per prefix een vestigingnaam op</div>
                  <div className="space-y-2">
                    {preview.prefixes.map(p => (
                      <div key={p.prefix} className="flex items-center gap-3">
                        <span className="text-xs text-slate-400 w-8 text-right">{p.count}x</span>
                        <span className="text-sm font-mono font-bold text-slate-600 dark:text-slate-300 w-16">{p.prefix}</span>
                        <span className="text-slate-400">→</span>
                        <input className={inputClass + ' flex-1'} value={prefixNames[p.prefix] || ''}
                          onChange={e => setPrefixNames(m => ({ ...m, [p.prefix]: e.target.value }))}
                          placeholder={`Vestigingnaam voor ${p.prefix}`} />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {preview.clusters.length > 0 && (
                <div>
                  <div className="text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Clusters uit bestand</div>
                  <div className="flex flex-wrap gap-2">
                    {preview.clusters.map(c => (
                      <span key={c.cluster} className="text-xs bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded px-2 py-1">
                        {c.cluster} ({c.count})
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {importError && <p className="text-red-500 text-sm">{importError}</p>}
          {importMsg && <p className="text-emerald-600 text-sm font-medium">{importMsg}</p>}

          {preview && (
            <button type="button" onClick={handleImport} disabled={importing} className={btnClass}>
              {importing ? 'Importeren...' : `Importeren (${preview.total} kluisjes)`}
            </button>
          )}
        </div>
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
  // Magister config
  const [magUrl, setMagUrl] = useState('')
  const [magUser, setMagUser] = useState('')
  const [magPass, setMagPass] = useState('')
  const [magPassSet, setMagPassSet] = useState(false)
  const [magSaving, setMagSaving] = useState(false)
  const [magMsg, setMagMsg] = useState('')

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
    api.get('/api/magister/config')
      .then(data => {
        setMagUrl(data.magister_url || '')
        setMagUser(data.magister_user || '')
        setMagPassSet(data.magister_pass_set)
      })
      .catch(() => {})
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

  async function handleSaveMagister(e) {
    e.preventDefault(); setMagSaving(true); setMagMsg('')
    try {
      const body = { magister_url: magUrl, magister_user: magUser }
      if (magPass) body.magister_pass = magPass
      await api.put('/api/magister/config', body)
      setMagPass('')
      setMagPassSet(true)
      setMagMsg('Opgeslagen!')
      setTimeout(() => setMagMsg(''), 3000)
    } catch (err) { setMagMsg(`Fout: ${err.message}`) }
    finally { setMagSaving(false) }
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

      <div className={cardClass}>
        <h2 className="text-base font-bold text-slate-800 dark:text-white mb-2">Magister API koppeling</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
          Koppel de Magister Medius webservice om leerlinggegevens automatisch te synchroniseren. De URL is meestal <code className="text-xs bg-slate-100 dark:bg-slate-700 px-1 rounded">https://jouwschool.swp.nl:8800/doc</code>
        </p>
        <form onSubmit={handleSaveMagister} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1.5 font-medium">Webservice URL</label>
            <input className={inputClass} value={magUrl} onChange={e => setMagUrl(e.target.value)}
              placeholder="https://jouwschool.swp.nl:8800/doc" />
          </div>
          <div>
            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1.5 font-medium">Gebruikersnaam</label>
            <input className={inputClass} value={magUser} onChange={e => setMagUser(e.target.value)}
              placeholder="webuser" />
          </div>
          <div>
            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1.5 font-medium">
              Wachtwoord {magPassSet && !magPass && <span className="text-emerald-600 font-normal">(ingesteld, laat leeg om te behouden)</span>}
            </label>
            <input type="password" className={inputClass} value={magPass} onChange={e => setMagPass(e.target.value)}
              placeholder={magPassSet ? '••••••••' : 'Wachtwoord'} />
          </div>
          <div className="flex items-center gap-3">
            <button type="submit" disabled={magSaving} className={btnClass}>
              {magSaving ? 'Opslaan...' : 'Opslaan'}
            </button>
            {magMsg && (
              <span className={`text-sm font-medium ${magMsg.startsWith('Fout') ? 'text-red-500' : 'text-emerald-600'}`}>
                {magMsg}
              </span>
            )}
          </div>
        </form>
      </div>

      {/* Backups */}
      <BackupPanel />

    </div>
  )
}

function BackupPanel() {
  const [backups, setBackups] = useState([])
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')
  const [restoreName, setRestoreName] = useState('')
  const [restoreConfirm, setRestoreConfirm] = useState('')
  const [restoring, setRestoring] = useState(false)
  const [showAll, setShowAll] = useState(false)

  const cardClass = "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6"
  const btnClass = "bg-primary text-white rounded-lg px-5 py-2.5 text-sm font-semibold hover:bg-primary-600 disabled:opacity-50 transition-colors"

  function load() {
    api.get('/api/backups').then(setBackups).catch(e => setErr(e.message))
  }
  useEffect(() => { load() }, [])

  function formatSize(n) {
    if (n < 1024) return `${n} B`
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
    return `${(n / 1024 / 1024).toFixed(1)} MB`
  }

  function formatDatum(iso) {
    const d = new Date(iso)
    return d.toLocaleString('nl-NL', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  async function maakBackup() {
    setLoading(true); setMsg(''); setErr('')
    try {
      const res = await api.post('/api/backups/create', {})
      setMsg(`Backup gemaakt: ${res.naam}`)
      load()
    } catch (e) { setErr(e.message) }
    finally { setLoading(false) }
  }

  async function doRestore() {
    if (restoreConfirm !== 'RESTORE') { setErr('Typ RESTORE om te bevestigen'); return }
    setRestoring(true); setMsg(''); setErr('')
    try {
      const res = await api.post(`/api/backups/${encodeURIComponent(restoreName)}/restore`, { bevestiging: 'RESTORE' })
      setMsg(`Teruggezet vanuit ${res.restored_from}. Safety-backup: ${res.safety_backup}`)
      setRestoreName(''); setRestoreConfirm('')
      load()
    } catch (e) { setErr(e.message) }
    finally { setRestoring(false) }
  }

  const laatste = backups[0]

  return (
    <div className={cardClass} style={{ marginTop: '1.25rem' }}>
      <h2 className="text-base font-bold text-slate-800 dark:text-white mb-1">Backups</h2>
      <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
        De database wordt automatisch dagelijks geback-upt (7 dagelijks + 4 wekelijks bewaard).
      </p>

      <div className="mb-4 text-sm">
        {laatste ? (
          <span className="text-slate-600 dark:text-slate-300">
            Laatste backup: <strong>{formatDatum(laatste.datum)}</strong> ({formatSize(laatste.grootte)}) — <span className="font-mono text-xs text-slate-400">{laatste.naam}</span>
          </span>
        ) : (
          <span className="text-slate-400">Nog geen backups.</span>
        )}
      </div>

      <div className="flex items-center gap-3 mb-4">
        <button onClick={maakBackup} disabled={loading} className={btnClass}>
          {loading ? 'Bezig...' : 'Nu backup maken'}
        </button>
        {msg && <span className="text-sm text-emerald-600 font-medium">{msg}</span>}
        {err && <span className="text-sm text-red-500 font-medium">Fout: {err}</span>}
      </div>

      {backups.length > 0 && (
        <div className="border-t border-slate-100 dark:border-slate-700 pt-4">
          <button onClick={() => setShowAll(v => !v)}
            className="w-full flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-wider hover:text-slate-700 dark:hover:text-slate-200">
            <span>Alle backups ({backups.length})</span>
            <span className="text-base">{showAll ? '▲' : '▼'}</span>
          </button>
          <div className={`${showAll ? 'block' : 'hidden'} space-y-1 max-h-64 overflow-y-auto`}>
            {backups.map(b => (
              <div key={b.naam} className="flex items-center justify-between text-sm py-1.5 px-2 hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded">
                <div className="flex-1 min-w-0">
                  <div className="font-mono text-xs text-slate-600 dark:text-slate-300 truncate">{b.naam}</div>
                  <div className="text-xs text-slate-400">{formatDatum(b.datum)} — {formatSize(b.grootte)}</div>
                </div>
                <div className="flex items-center gap-2 ml-3">
                  <a href={`/api/backups/${encodeURIComponent(b.naam)}/download`}
                    className="text-xs px-2 py-1 rounded border border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700">
                    Download
                  </a>
                  <button onClick={() => { setRestoreName(b.naam); setRestoreConfirm(''); setErr(''); setMsg('') }}
                    className="text-xs px-2 py-1 rounded border border-red-300 text-red-600 hover:bg-red-50 dark:border-red-700 dark:text-red-400 dark:hover:bg-red-900/20">
                    Terugzetten
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {restoreName && (
        <div className="mt-4 p-4 border-2 border-red-300 dark:border-red-700 rounded-xl bg-red-50 dark:bg-red-900/20">
          <div className="text-sm font-semibold text-red-700 dark:text-red-400 mb-1">Database terugzetten</div>
          <p className="text-xs text-red-600 dark:text-red-300 mb-3">
            Je staat op het punt de huidige database te vervangen door <span className="font-mono">{restoreName}</span>.
            Alle huidige data wordt overschreven (er wordt eerst een safety-backup gemaakt).
            Typ <strong>RESTORE</strong> om te bevestigen.
          </p>
          <div className="flex items-center gap-2">
            <input className="border border-red-300 dark:border-red-700 rounded-lg px-3 py-1.5 text-sm bg-white dark:bg-slate-700 dark:text-white"
              value={restoreConfirm} onChange={e => setRestoreConfirm(e.target.value)} placeholder="Typ RESTORE" />
            <button onClick={doRestore} disabled={restoring || restoreConfirm !== 'RESTORE'}
              className="bg-red-600 text-white rounded-lg px-4 py-1.5 text-sm font-semibold hover:bg-red-700 disabled:opacity-50">
              {restoring ? 'Terugzetten...' : 'Ja, terugzetten'}
            </button>
            <button onClick={() => { setRestoreName(''); setRestoreConfirm('') }}
              className="text-sm px-3 py-1.5 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700">
              Annuleren
            </button>
          </div>
        </div>
      )}
    </div>
  )
}


// ── Gebruikers ──────────────────────────────────────────────────────────────

function GebruikersTab() {
  const [gebruikers, setGebruikers] = useState([])
  const [vestigingen, setVestigingen] = useState([])
  const [email, setEmail] = useState('')
  const [naam, setNaam] = useState('')
  const [rol, setRol] = useState('concierge')
  const [selVestigingen, setSelVestigingen] = useState([])
  const [editId, setEditId] = useState(null)
  const [editNaam, setEditNaam] = useState('')
  const [editRol, setEditRol] = useState('concierge')
  const [editVestigingen, setEditVestigingen] = useState([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  function load() {
    api.get('/api/gebruikers').then(setGebruikers).catch(() => {})
    api.get('/api/vestigingen').then(setVestigingen).catch(() => {})
  }
  useEffect(() => { load() }, [])

  async function handleAdd(e) {
    e.preventDefault(); setError(''); setSuccess('')
    try {
      await api.post('/api/gebruikers', { email, naam, rol, vestiging_ids: rol === 'concierge' ? selVestigingen : [] })
      setEmail(''); setNaam(''); setRol('concierge'); setSelVestigingen([])
      setSuccess(`${email} is toegevoegd`)
      load()
    } catch (err) { setError(err.message) }
  }

  async function handleUpdate(id) {
    setError(''); setSuccess('')
    try {
      await api.put(`/api/gebruikers/${id}`, { naam: editNaam, rol: editRol, vestiging_ids: editRol === 'concierge' ? editVestigingen : [] })
      setEditId(null); load()
    } catch (err) { setError(err.message) }
  }

  async function handleDelete(id) {
    setError(''); setSuccess('')
    try { await api.del(`/api/gebruikers/${id}`); load() }
    catch (err) { setError(err.message) }
  }

  async function handleToggleActief(g) {
    try { await api.put(`/api/gebruikers/${g.id}`, { naam: g.naam, rol: g.rol, actief: !g.actief, vestiging_ids: g.vestiging_ids }); load() }
    catch (err) { setError(err.message) }
  }

  return (
    <div className="max-w-3xl">
      <h2 className="text-base font-bold text-navy dark:text-white mb-1">Gebruikers</h2>
      <p className="text-sm text-slate-500 dark:text-slate-400 mb-5">
        Voeg gebruikers toe via hun e-mailadres. Zij moeten ook lid zijn van de Entra-groep voor kluisjesbeheer.
      </p>

      {error && <p className="text-red-500 text-sm mb-3 bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded-lg">{error}</p>}
      {success && <p className="text-emerald-600 text-sm mb-3 bg-emerald-50 dark:bg-emerald-900/20 px-3 py-2 rounded-lg">{success}</p>}

      {/* Bestaande gebruikers */}
      <div className="space-y-3 mb-6">
        {gebruikers.map(g => (
          <div key={g.id} className={`border rounded-xl p-4 transition-all ${!g.actief ? 'opacity-50 border-slate-200 dark:border-slate-700' : 'border-slate-200 dark:border-slate-700'}`}>
            {editId === g.id ? (
              <div className="space-y-3">
                <div className="text-sm font-medium text-slate-500">{g.email}</div>
                <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white"
                  value={editNaam} onChange={e => setEditNaam(e.target.value)} placeholder="Naam" />
                <div className="flex gap-3">
                  <label className="flex items-center gap-1.5 text-sm cursor-pointer">
                    <input type="radio" name="editRol" value="beheerder" checked={editRol === 'beheerder'} onChange={() => setEditRol('beheerder')} />
                    Beheerder
                  </label>
                  <label className="flex items-center gap-1.5 text-sm cursor-pointer">
                    <input type="radio" name="editRol" value="concierge" checked={editRol === 'concierge'} onChange={() => setEditRol('concierge')} />
                    Conciërge
                  </label>
                </div>
                {editRol === 'concierge' && (
                  <div>
                    <div className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-1">Vestigingen</div>
                    <div className="flex flex-wrap gap-2">
                      {vestigingen.map(v => (
                        <label key={v.id} className="flex items-center gap-1.5 text-sm cursor-pointer">
                          <input type="checkbox" checked={editVestigingen.includes(v.id)}
                            onChange={() => setEditVestigingen(prev => prev.includes(v.id) ? prev.filter(x => x !== v.id) : [...prev, v.id])}
                            className="rounded border-slate-300" />
                          {v.naam}
                        </label>
                      ))}
                    </div>
                  </div>
                )}
                <div className="flex gap-2">
                  <button onClick={() => handleUpdate(g.id)}
                    className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary-600">Opslaan</button>
                  <button onClick={() => setEditId(null)}
                    className="px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm text-slate-600 dark:text-slate-300">Annuleren</button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold text-sm">{g.naam || g.email}</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">{g.email}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`inline-block px-2 py-0.5 text-xs rounded-full font-medium ${
                      g.rol === 'beheerder' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300' : 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300'
                    }`}>{g.rol === 'beheerder' ? 'Beheerder' : 'Conciërge'}</span>
                    {g.rol === 'concierge' && g.vestiging_ids.length > 0 && (
                      <span className="text-xs text-slate-500">
                        {g.vestiging_ids.map(vid => vestigingen.find(v => v.id === vid)?.naam || vid).join(', ')}
                      </span>
                    )}
                    {g.rol === 'concierge' && g.vestiging_ids.length === 0 && (
                      <span className="text-xs text-amber-500 font-medium">Geen vestigingen!</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => handleToggleActief(g)}
                    className={`text-xs px-2 py-1 rounded-lg border ${g.actief ? 'border-slate-300 text-slate-500 hover:border-amber-300 hover:text-amber-600' : 'border-emerald-300 text-emerald-600 hover:bg-emerald-50'}`}>
                    {g.actief ? 'Deactiveer' : 'Activeer'}
                  </button>
                  <button onClick={() => { setEditId(g.id); setEditNaam(g.naam); setEditRol(g.rol); setEditVestigingen(g.vestiging_ids) }}
                    className="text-slate-400 hover:text-primary p-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                  </button>
                  <ConfirmButton onConfirm={() => handleDelete(g.id)}
                    className="text-slate-400 hover:text-red-500 p-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </ConfirmButton>
                </div>
              </div>
            )}
          </div>
        ))}
        {gebruikers.length === 0 && <p className="text-sm text-slate-400">Nog geen gebruikers. Voeg jezelf eerst toe als beheerder.</p>}
      </div>

      {/* Nieuwe gebruiker */}
      <form onSubmit={handleAdd} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5 space-y-3">
        <div className="text-sm font-bold text-navy dark:text-white">Gebruiker toevoegen</div>
        <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white"
          type="email" placeholder="E-mailadres" value={email} onChange={e => setEmail(e.target.value)} required />
        <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white"
          placeholder="Naam (optioneel)" value={naam} onChange={e => setNaam(e.target.value)} />
        <div className="flex gap-3">
          <label className="flex items-center gap-1.5 text-sm cursor-pointer">
            <input type="radio" name="rol" value="beheerder" checked={rol === 'beheerder'} onChange={() => setRol('beheerder')} />
            Beheerder
          </label>
          <label className="flex items-center gap-1.5 text-sm cursor-pointer">
            <input type="radio" name="rol" value="concierge" checked={rol === 'concierge'} onChange={() => setRol('concierge')} />
            Conciërge
          </label>
        </div>
        {rol === 'concierge' && (
          <div>
            <div className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-1">Vestigingen</div>
            <div className="flex flex-wrap gap-2">
              {vestigingen.map(v => (
                <label key={v.id} className="flex items-center gap-1.5 text-sm cursor-pointer">
                  <input type="checkbox" checked={selVestigingen.includes(v.id)}
                    onChange={() => setSelVestigingen(prev => prev.includes(v.id) ? prev.filter(x => x !== v.id) : [...prev, v.id])}
                    className="rounded border-slate-300" />
                  {v.naam}
                </label>
              ))}
            </div>
          </div>
        )}
        <button type="submit"
          className="w-full bg-primary text-white rounded-lg py-2.5 text-sm font-semibold hover:bg-primary-600 transition-colors">
          + Gebruiker toevoegen
        </button>
      </form>
    </div>
  )
}

const TABS = ['Instellingen', 'Import', 'Vestigingen', 'Gebruikers']

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
      {activeTab === 0 && <BeheerInstellingenTab />}
      {activeTab === 1 && <ImportTab />}
      {activeTab === 2 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5">
            <VestigingenPanel onSelect={id => { setSelectedVestiging(id); setSelectedCluster(null) }} selectedId={selectedVestiging} />
          </div>
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5">
            <ClustersPanel vestigingId={selectedVestiging} onSelect={setSelectedCluster} selectedId={selectedCluster} />
          </div>
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5">
            <KluisjesPanel clusterId={selectedCluster} vestigingId={selectedVestiging} />
          </div>
        </div>
      )}
      {activeTab === 3 && <GebruikersTab />}
    </div>
  )
}
