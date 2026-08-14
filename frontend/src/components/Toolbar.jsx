import { useState, useEffect } from 'react'
import { useInstellingen } from '../context/InstellingenContext'
import { api } from '../api'

// As 1 — Status: wat het kluisje IS (precies één, bepaalt de tegelkleur).
const statusOptions = [
  { value: '', label: 'Alles' },
  { value: 'vrij', label: 'Vrij', dot: 'bg-emerald-500' },
  { value: 'uitgeleend', label: 'Uitgeleend', dot: 'bg-sky-400' },
  { value: 'defect', label: 'Defect', dot: 'bg-amber-500' },
  { value: 'geen_sleutel', label: 'Geen sleutel', dot: 'bg-slate-400' },
]

// As 2 — Aandachtspunten: vlaggen die op een kluisje kunnen liggen (kunnen
// stapelen), los van de hoofdstatus. Eén dropdown houdt de chip-balk kort.
// Iconen komen overeen met de tegels en de legenda.
const aandachtspunten = [
  { value: 'borg', label: 'Borg openstaand', icon: '💰' },
  { value: 'sleutel_niet_ingeleverd', label: 'Sleutel niet ingeleverd', icon: '🔑' },
  { value: 'vertrokken', label: 'Vertrokken', icon: '⚠' },
  { value: 'reservesleutel', label: 'Reservesleutel uitgegeven', icon: '🗝️' },
]

const EyeIcon = () => (
  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
  </svg>
)

function RapportRij({ label, type, onDownload, onPreview }) {
  return (
    <div className="flex items-center justify-between pr-2">
      <button onClick={() => onDownload(type)} className="flex-1 text-left px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700">{label}</button>
      <button onClick={() => onPreview(type)} className="text-slate-400 hover:text-primary px-2 py-1" title="Preview"><EyeIcon /></button>
    </div>
  )
}

function RapportDropdown({ vestigingId, klas, klassen }) {
  const [open, setOpen] = useState(false)
  const [selectie, setSelectie] = useState([])
  const { borgActiefVoor } = useInstellingen()

  // Een array-waarde wordt herhaald in de querystring (klas=M4A&klas=M4B), want
  // het per-klas rapport accepteert meerdere klassen in één PDF.
  function bouwParams(type, extra) {
    const params = new URLSearchParams({ type })
    if (vestigingId) params.set('vestiging_id', vestigingId)
    Object.entries(extra).forEach(([k, v]) => {
      if (Array.isArray(v)) v.forEach(item => item && params.append(k, item))
      else if (v) params.set(k, v)
    })
    return params
  }

  function download(type, extra = {}) {
    window.open(`/api/dashboard/rapport?${bouwParams(type, extra)}`, '_blank')
    setOpen(false)
  }

  function preview(type, extra = {}) {
    window.open(`/api/dashboard/rapport/preview?${bouwParams(type, extra)}`, '_blank')
    setOpen(false)
  }

  function toggleKlas(k) {
    setSelectie(s => s.includes(k) ? s.filter(x => x !== k) : [...s, k])
  }

  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)}
        className="border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-1.5 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 flex items-center gap-1.5 transition-colors">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Rapport
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 mt-2 z-20 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-lg py-2 w-72">
            <div className="px-4 py-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wide">Overzichten</div>
            <RapportRij label="Actieve toewijzingen" type="toewijzingen" onDownload={download} onPreview={preview} />
            <RapportRij label="Innameoverzicht (afvinklijst)" type="inname" onDownload={download} onPreview={preview} />
            <RapportRij label="Defecte kluisjes" type="defect" onDownload={download} onPreview={preview} />
            <RapportRij label="Leerlingen zonder kluisje" type="zonder_kluisje" onDownload={download} onPreview={preview} />
            <div className="border-t border-slate-100 dark:border-slate-700 my-1" />
            <div className="px-4 py-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wide">Openstaand</div>
            <RapportRij label="Openstaande sleutels" type="sleutels" onDownload={download} onPreview={preview} />
            <RapportRij label="Vertrokken met sleutel (per klas)" type="vertrokken" onDownload={download} onPreview={preview} />
            {borgActiefVoor(vestigingId) && (
              <RapportRij label="Openstaande borg" type="borg" onDownload={download} onPreview={preview} />
            )}
            <div className="border-t border-slate-100 dark:border-slate-700 my-1" />
            <div className="px-4 py-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wide">Per klas</div>
            {klas ? (
              <div className="flex items-center justify-between pr-2">
                <button onClick={() => download('klas', { klas })}
                  className="flex-1 text-left px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700">
                  Huidige klas ({klas})
                </button>
                <button onClick={() => preview('klas', { klas })} className="text-slate-400 hover:text-primary px-2 py-1" title="Preview"><EyeIcon /></button>
              </div>
            ) : (
              <div className="px-4 py-1.5 text-xs text-slate-400">Kies eerst een klas in de filterbalk voor één klas</div>
            )}
            <div className="flex items-center justify-between pr-2">
              <button onClick={() => download('klas')}
                className="flex-1 text-left px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700">
                Alle klassen
              </button>
              <button onClick={() => preview('klas')} className="text-slate-400 hover:text-primary px-2 py-1" title="Preview"><EyeIcon /></button>
            </div>

            {klassen.length > 0 && (
              <div className="border-t border-slate-100 dark:border-slate-700 mt-1 pt-1">
                <div className="flex items-center justify-between px-4 py-1.5">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Selectie</span>
                  <button
                    onClick={() => setSelectie(s => s.length === klassen.length ? [] : [...klassen])}
                    className="text-xs text-primary hover:underline">
                    {selectie.length === klassen.length ? 'Niets' : 'Alles'}
                  </button>
                </div>
                <div className="max-h-44 overflow-y-auto px-4 py-1">
                  {klassen.map(k => (
                    <label key={k} className="flex items-center gap-2 py-1 text-sm cursor-pointer">
                      <input type="checkbox" checked={selectie.includes(k)} onChange={() => toggleKlas(k)}
                        className="rounded border-slate-300 text-primary focus:ring-primary/30" />
                      <span>{k}</span>
                    </label>
                  ))}
                </div>
                <div className="flex items-center justify-between pr-2">
                  <button disabled={selectie.length === 0}
                    onClick={() => download('klas', { klas: selectie })}
                    className="flex-1 text-left px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700 disabled:text-slate-300 dark:disabled:text-slate-600 disabled:hover:bg-transparent">
                    Download selectie ({selectie.length})
                  </button>
                  <button disabled={selectie.length === 0}
                    onClick={() => preview('klas', { klas: selectie })}
                    className="text-slate-400 hover:text-primary px-2 py-1 disabled:text-slate-200 dark:disabled:text-slate-700"
                    title="Preview"><EyeIcon /></button>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

function AandachtspuntenDropdown({ filters, setFilters }) {
  const [open, setOpen] = useState(false)
  const active = aandachtspunten.some(s => s.value === filters.status)
  const activeItem = aandachtspunten.find(s => s.value === filters.status)

  return (
    <div className="relative">
      <button onClick={() => setOpen(o => !o)}
        className={`flex items-center gap-1.5 px-3 py-1 text-xs rounded-md transition-colors ${
          active
            ? 'bg-white dark:bg-slate-600 text-navy dark:text-white font-medium shadow-sm'
            : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
        }`}>
        {active ? <><span aria-hidden="true">{activeItem.icon}</span>{activeItem.label}</> : 'Aandachtspunten'}
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute left-0 mt-2 z-20 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-lg py-1 w-60">
            {aandachtspunten.map(s => (
              <button key={s.value}
                onClick={() => { setFilters(f => ({ ...f, status: s.value })); setOpen(false) }}
                className={`w-full text-left px-4 py-2 text-sm flex items-center gap-2 hover:bg-slate-50 dark:hover:bg-slate-700 ${
                  filters.status === s.value ? 'text-primary font-medium' : 'text-slate-600 dark:text-slate-300'
                }`}>
                <span aria-hidden="true">{s.icon}</span>{s.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default function Toolbar({ clusters, filters, setFilters, onBulkAssign, onBulkEnd, vestigingId }) {
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [klassen, setKlassen] = useState([])

  useEffect(() => {
    if (!vestigingId) { setKlassen([]); return }
    api.get(`/api/vestigingen/${vestigingId}/klassen`).then(setKlassen).catch(() => setKlassen([]))
  }, [vestigingId])

  const selectClass = "border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-1.5 text-sm bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-primary/30 focus:border-primary outline-none"

  return (
    <div className="border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-2.5">
      <div className="flex flex-wrap gap-2 items-center">
        {/* Cluster */}
        <select className={selectClass} value={filters.cluster_id || ''}
          onChange={e => setFilters(f => ({ ...f, cluster_id: e.target.value || null }))}>
          <option value="">Alle clusters</option>
          {clusters.map(c => <option key={c.id} value={c.id}>{c.naam}</option>)}
        </select>

        {/* Klas */}
        <select className={selectClass} value={filters.klas || ''}
          onChange={e => setFilters(f => ({ ...f, klas: e.target.value }))}>
          <option value="">Alle klassen</option>
          {klassen.map(k => <option key={k} value={k}>{k}</option>)}
        </select>

        {/* Search */}
        <div className="flex-1 min-w-[200px] relative">
          <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            className="w-full border border-slate-300 dark:border-slate-600 rounded-lg pl-8 pr-3 py-1.5 text-sm dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-primary/30 focus:border-primary outline-none"
            placeholder="Zoek kluisnr, naam, stamnr..."
            value={filters.q}
            onChange={e => setFilters(f => ({ ...f, q: e.target.value }))}
          />
        </div>

        {/* Mobile filters toggle */}
        <button className="md:hidden border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-1.5 text-sm text-slate-500 dark:text-slate-400"
          onClick={() => setFiltersOpen(!filtersOpen)}>
          Filters {filtersOpen ? '▲' : '▼'}
        </button>

        {/* Status filters */}
        <div className={`${filtersOpen ? 'flex' : 'hidden'} md:flex gap-1 bg-slate-100 dark:bg-slate-700 rounded-lg p-0.5`}>
          {statusOptions.map(s => (
            <button key={s.value} onClick={() => setFilters(f => ({ ...f, status: s.value }))}
              className={`flex items-center gap-1.5 px-3 py-1 text-xs rounded-md transition-colors ${
                filters.status === s.value
                  ? 'bg-white dark:bg-slate-600 text-navy dark:text-white font-medium shadow-sm'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
              }`}>
              {s.dot && <span className={`w-2 h-2 rounded-full ${s.dot}`} />}
              {s.label}
            </button>
          ))}
          <span className="w-px h-4 bg-slate-300 dark:bg-slate-500 mx-0.5" aria-hidden="true" />
          <AandachtspuntenDropdown filters={filters} setFilters={setFilters} />
        </div>

        {/* View toggle */}
        <div className="flex bg-slate-100 dark:bg-slate-700 rounded-lg p-0.5">
          <button onClick={() => setFilters(f => ({ ...f, view: 'table' }))}
            className={`px-2.5 py-1 text-xs rounded-md transition-colors ${filters.view === 'table' ? 'bg-white dark:bg-slate-600 text-navy dark:text-white shadow-sm' : 'text-slate-400'}`}
            title="Tabelweergave">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
            </svg>
          </button>
          <button onClick={() => setFilters(f => ({ ...f, view: 'grid' }))}
            className={`px-2.5 py-1 text-xs rounded-md transition-colors ${filters.view === 'grid' ? 'bg-white dark:bg-slate-600 text-navy dark:text-white shadow-sm' : 'text-slate-400'}`}
            title="Gridweergave">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
            </svg>
          </button>
        </div>

        {/* Bulk actions */}
        {onBulkAssign && (
          <button onClick={onBulkAssign}
            className="bg-primary text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-primary-600 transition-colors">
            Collectief toekennen
          </button>
        )}
        {onBulkEnd && (
          <button onClick={onBulkEnd}
            className="border-2 border-red-400 text-red-600 dark:text-red-400 px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
            Collectief beëindigen
          </button>
        )}

        {/* Rapport */}
        <RapportDropdown vestigingId={vestigingId} klas={filters.klas} klassen={klassen} />
      </div>
    </div>
  )
}
