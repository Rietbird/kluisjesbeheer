import { useState, useEffect } from 'react'
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
          className="px-3 py-1.5 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50">Nee</button>
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
            className={`border-2 rounded-xl p-3 cursor-pointer transition-all ${selectedId === v.id ? 'border-School bg-School-50' : 'border-slate-200 dark:border-slate-600 hover:border-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'}`}>
            {editId === v.id ? (
              <div className="space-y-2">
                <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" value={editNaam}
                  onChange={e => setEditNaam(e.target.value)} placeholder="Naam" />
                <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" value={editAdres}
                  onChange={e => setEditAdres(e.target.value)} placeholder="Adres" />
                <div className="flex gap-2 mt-2">
                  <button onClick={() => handleUpdate(v.id)}
                    className="px-4 py-2 bg-School text-white rounded-lg text-sm font-medium hover:bg-School-600">Opslaan</button>
                  <button onClick={() => setEditId(null)}
                    className="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50">Annuleren</button>
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
                    className="text-slate-400 hover:text-School p-1 rounded hover:bg-slate-100 transition-colors">
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
        <div className="text-sm font-semibold text-slate-600 mb-1">Nieuwe vestiging</div>
        <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" placeholder="Naam" value={naam}
          onChange={e => setNaam(e.target.value)} required />
        <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" placeholder="Adres (optioneel)" value={adres}
          onChange={e => setAdres(e.target.value)} />
        <button type="submit"
          className="w-full bg-School text-white rounded-lg py-2.5 text-sm font-semibold hover:bg-School-600 transition-colors">
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
            className={`border-2 rounded-xl p-3 cursor-pointer transition-all ${selectedId === c.id ? 'border-School bg-School-50' : 'border-slate-200 dark:border-slate-600 hover:border-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'}`}>
            {editId === c.id ? (
              <div className="space-y-2">
                <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" value={editNaam}
                  onChange={e => setEditNaam(e.target.value)} placeholder="Naam" />
                <input type="number" step="0.01" className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" value={editBorg}
                  onChange={e => setEditBorg(e.target.value)} placeholder="Standaard borg (€)" />
                <div className="flex gap-2 mt-2">
                  <button onClick={() => handleUpdate(c.id)}
                    className="px-4 py-2 bg-School text-white rounded-lg text-sm font-medium hover:bg-School-600">Opslaan</button>
                  <button onClick={() => setEditId(null)}
                    className="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50">Annuleren</button>
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
                    className="text-slate-400 hover:text-School p-1 rounded hover:bg-slate-100 transition-colors">
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
        <div className="text-sm font-semibold text-slate-600 mb-1">Nieuw cluster</div>
        <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" placeholder="Naam" value={naam}
          onChange={e => setNaam(e.target.value)} required />
        <input type="number" step="0.01" className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white"
          placeholder="Standaard borg (€)" value={borg} onChange={e => setBorg(e.target.value)} />
        <button type="submit"
          className="w-full bg-School text-white rounded-lg py-2.5 text-sm font-semibold hover:bg-School-600 transition-colors">
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

  if (!clusterId) return (
    <div>
      <h2 className="text-base font-bold text-navy dark:text-white mb-4">Kluisjes</h2>
      <p className="text-sm text-slate-400">Selecteer een cluster.</p>
    </div>
  )

  return (
    <div>
      <h2 className="text-base font-bold text-navy dark:text-white mb-4">Kluisjes</h2>
      {error && <p className="text-red-500 text-sm mb-3">{error}</p>}
      <div className="space-y-1.5 mb-5 max-h-96 overflow-y-auto">
        {kluisjes.map(k => (
          <div key={k.id} className="border border-slate-200 rounded-xl p-3 hover:bg-slate-50 transition-colors">
            {editId === k.id ? (
              <div className="space-y-2">
                <div className="text-sm font-semibold text-navy">Kluisje {k.kluisnummer}</div>
                <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" value={editData.sleutelnummer || ''}
                  onChange={e => setEditData(d => ({ ...d, sleutelnummer: e.target.value }))} placeholder="Sleutelnr" />
                <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" value={editData.locatie || ''}
                  onChange={e => setEditData(d => ({ ...d, locatie: e.target.value }))} placeholder="Locatie" />
                <div className="flex gap-2 mt-2">
                  <button onClick={() => handleUpdate(k.id)}
                    className="px-4 py-2 bg-School text-white rounded-lg text-sm font-medium hover:bg-School-600">Opslaan</button>
                  <button onClick={() => setEditId(null)}
                    className="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50">Annuleren</button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="font-semibold text-navy">{k.kluisnummer}</span>
                  {k.sleutelnummer && <span className="text-sm text-slate-500">sleutel {k.sleutelnummer}</span>}
                  <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                    k.status === 'uitgeleend' ? 'bg-emerald-100 text-emerald-700' :
                    k.status === 'defect' ? 'bg-amber-100 text-amber-700' :
                    'bg-sky-100 text-sky-700'
                  }`}>{k.status}</span>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => { setEditId(k.id); setEditData({ sleutelnummer: k.sleutelnummer || '', locatie: k.locatie || '' }) }}
                    className="text-slate-400 hover:text-School p-1 rounded hover:bg-slate-100 transition-colors">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                  </button>
                  <ConfirmButton onConfirm={() => handleDelete(k.id)}
                    className="text-slate-400 hover:text-red-500 p-1 rounded hover:bg-slate-100 transition-colors">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </ConfirmButton>
                </div>
              </div>
            )}
          </div>
        ))}
        {kluisjes.length === 0 && <p className="text-sm text-slate-400">Nog geen kluisjes in dit cluster.</p>}
      </div>
      <form onSubmit={handleAdd} className="space-y-2 border-t border-slate-200 pt-4">
        <div className="text-sm font-semibold text-slate-600 mb-1">Nieuw kluisje</div>
        <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" placeholder="Kluisnummer" value={kluisnummer}
          onChange={e => setKluisnummer(e.target.value)} required />
        <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" placeholder="Sleutelnummer (optioneel)"
          value={sleutelnummer} onChange={e => setSleutelnummer(e.target.value)} />
        <input className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white" placeholder="Locatie (optioneel)"
          value={locatie} onChange={e => setLocatie(e.target.value)} />
        <button type="submit"
          className="w-full bg-School text-white rounded-lg py-2.5 text-sm font-semibold hover:bg-School-600 transition-colors">
          + Toevoegen
        </button>
      </form>
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
        className="w-full bg-School text-white rounded-lg py-2.5 text-sm font-semibold hover:bg-School-600 disabled:opacity-50 transition-colors flex items-center justify-center gap-2">
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

// ── Borg Tab ──────────────────────────────────────────────────────────────────

function BorgTab() {
  const { borgActiefVoor, setBorgActiefVoor } = useInstellingen()
  const [vestigingen, setVestigingen] = useState([])
  const [clusters, setClusters] = useState({})
  const [editId, setEditId] = useState(null)
  const [editBorg, setEditBorg] = useState('')
  const [saving, setSaving] = useState(null)

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
    } catch {}
  }

  const cardClass = "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5"
  const inputClass = "border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-1.5 text-sm bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-School/30 focus:border-School outline-none w-32"

  return (
    <div className="space-y-5 max-w-2xl">
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
              className={`flex items-center w-14 h-7 rounded-full px-0.5 transition-colors focus:outline-none ${borgActiefVoor(v.id) ? 'bg-School' : 'bg-slate-300 dark:bg-slate-600'}`}
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
                          className="px-3 py-1.5 bg-School text-white rounded-lg text-sm hover:bg-School-600">Opslaan</button>
                        <button onClick={() => setEditId(null)}
                          className="px-3 py-1.5 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50">Annuleren</button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-3">
                        <span className="text-sm text-slate-500">
                          {c.standaard_borg != null ? `€${Number(c.standaard_borg).toFixed(2)}` : '—'}
                        </span>
                        <button onClick={() => { setEditId(c.id); setEditBorg(c.standaard_borg ?? '') }}
                          className="text-slate-400 hover:text-School p-1 rounded hover:bg-slate-100 transition-colors">
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
      setImportMsg(`Import geslaagd: ${res.imported ?? res.count ?? '?'} kluisjes geimporteerd.`)
      setImportFile(null)
      const fileInput = document.getElementById('xlsx-file-input-beheer')
      if (fileInput) fileInput.value = ''
    } catch (err) { setImportError(`Import mislukt: ${err.message}`) }
    finally { setImporting(false) }
  }

  const selectClass = "w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2.5 text-sm bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-School/30 focus:border-School outline-none"
  const btnClass = "bg-School text-white rounded-lg px-5 py-2.5 text-sm font-semibold hover:bg-School-600 disabled:opacity-50 transition-colors"
  const cardClass = "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6"

  return (
    <div className="max-w-2xl">
      <div className={cardClass}>
        <h2 className="text-base font-bold text-slate-800 dark:text-white mb-2">Import kluisjes</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
          Importeer kluisjes vanuit een Excel-bestand (.xlsx). Nieuwe kluisjes worden aangemaakt met status "vrij".
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
              className="w-full text-sm text-slate-600 dark:text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-School-50 dark:file:bg-School-700 file:text-School-700 dark:file:text-white hover:file:bg-School-100"
              onChange={e => setImportFile(e.target.files[0] || null)} />
          </div>

          <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4">
            <div className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Verwacht formaat</div>
            <div className="overflow-x-auto">
              <table className="text-xs border border-slate-200 dark:border-slate-600 rounded-lg overflow-hidden w-full">
                <thead>
                  <tr className="bg-School/10 dark:bg-School/20">
                    <th className="px-3 py-1.5 text-left font-bold text-slate-700 dark:text-slate-300">Cluster</th>
                    <th className="px-3 py-1.5 text-left font-bold text-slate-700 dark:text-slate-300">Kluis</th>
                    <th className="px-3 py-1.5 text-left font-bold text-slate-700 dark:text-slate-300">Naam</th>
                    <th className="px-3 py-1.5 text-left font-bold text-slate-700 dark:text-slate-300">Stamnummer</th>
                    <th className="px-3 py-1.5 text-left font-bold text-slate-700 dark:text-slate-300">Klas</th>
                    <th className="px-3 py-1.5 text-left font-bold text-slate-700 dark:text-slate-300">Status</th>
                    <th className="px-3 py-1.5 text-left font-bold text-slate-700 dark:text-slate-300">Sleutel</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-600">
                  <tr><td className="px-3 py-1.5">Kluisjes 25/26</td><td className="px-3 py-1.5">P001</td><td className="px-3 py-1.5">Jan de Vries</td><td className="px-3 py-1.5">21001</td><td className="px-3 py-1.5">3A</td><td className="px-3 py-1.5">Uitgeleend</td><td className="px-3 py-1.5">2040D</td></tr>
                  <tr><td className="px-3 py-1.5">Kluisjes 25/26</td><td className="px-3 py-1.5">P002</td><td className="px-3 py-1.5">Emma Bakker</td><td className="px-3 py-1.5">22002</td><td className="px-3 py-1.5">2B</td><td className="px-3 py-1.5">Uitgeleend</td><td className="px-3 py-1.5">2656D</td></tr>
                  <tr><td className="px-3 py-1.5">Zonder cluster</td><td className="px-3 py-1.5">X100</td><td className="px-3 py-1.5"></td><td className="px-3 py-1.5"></td><td className="px-3 py-1.5"></td><td className="px-3 py-1.5">Vrij</td><td className="px-3 py-1.5">X100</td></tr>
                </tbody>
              </table>
            </div>
            <div className="flex items-center gap-3 mt-3">
              <a href="/voorbeeld-import.xlsx" download
                className="text-sm text-School hover:text-School-700 font-medium flex items-center gap-1.5">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Voorbeeldbestand downloaden
              </a>
              <span className="text-xs text-slate-400">(.xlsx, 3 voorbeeldrijen)</span>
            </div>
          </div>

          {importError && <p className="text-red-500 text-sm">{importError}</p>}
          {importMsg && <p className="text-emerald-600 text-sm font-medium">{importMsg}</p>}
          <button type="submit" disabled={importing} className={btnClass}>
            {importing ? 'Importeren...' : 'Importeren'}
          </button>
        </form>
      </div>
    </div>
  )
}

// ── Instellingen Tab ──────────────────────────────────────────────────────────

function BeheerInstellingenTab() {
  const [periodeVan, setPeriodeVan] = useState('')
  const [periodeTot, setPeriodeTot] = useState('')
  const [regio, setRegio] = useState('noord')
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState('')
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    api.get('/api/instellingen')
      .then(data => {
        setPeriodeVan(data.standaard_periode_van || '')
        setPeriodeTot(data.standaard_periode_tot || '')
        setRegio(data.regio || 'noord')
      })
      .catch(() => {})
      .finally(() => setLoaded(true))
  }, [])

  async function handleSave(e) {
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

  const inputClass = "w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2.5 text-sm bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-School/30 focus:border-School outline-none transition-all"
  const btnClass = "bg-School text-white rounded-lg px-5 py-2.5 text-sm font-semibold hover:bg-School-600 disabled:opacity-50 transition-colors"
  const cardClass = "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6"

  if (!loaded) return <div className="p-4 text-sm text-slate-400">Laden...</div>

  return (
    <div className="max-w-2xl space-y-5">
      <div className={cardClass}>
        <h2 className="text-base font-bold text-slate-800 dark:text-white mb-4">Standaard uitleenperiode</h2>
        <form onSubmit={handleSave} className="space-y-4">
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
        <MagisterSyncPanel />
      </div>
    </div>
  )
}

const TABS = ['Vestigingen & Kluisjes', 'Borg', 'Import', 'Instellingen']

export default function Beheer({ onClose }) {
  const [activeTab, setActiveTab] = useState(0)
  const [selectedVestiging, setSelectedVestiging] = useState(null)
  const [selectedCluster, setSelectedCluster] = useState(null)

  return (
    <div className="fixed inset-0 z-50 flex flex-col">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative flex flex-col bg-gradient-to-b from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-950 w-full h-full overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-sm">
          <h1 className="text-xl font-bold text-navy dark:text-white">Beheer</h1>
          <button onClick={onClose}
            className="w-9 h-9 flex items-center justify-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-6 sm:p-8 max-w-6xl mx-auto">
            {/* Tab bar */}
            <div className="flex gap-1 border-b border-slate-200 dark:border-slate-700 mb-6">
              {TABS.map((tab, i) => (
                <button key={tab} onClick={() => setActiveTab(i)}
                  className={`px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors ${
                    activeTab === i
                      ? 'bg-white dark:bg-slate-800 border border-b-white dark:border-slate-700 dark:border-b-slate-800 text-School -mb-px'
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
            {activeTab === 2 && <ImportTab />}
            {activeTab === 3 && <BeheerInstellingenTab />}
          </div>
        </div>
      </div>
    </div>
  )
}
