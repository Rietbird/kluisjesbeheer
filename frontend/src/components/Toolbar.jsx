import { useState } from 'react'

const statusOptions = [
  { value: '', label: 'Alles' },
  { value: 'vrij', label: 'Vrij', dot: 'bg-sky-400' },
  { value: 'uitgeleend', label: 'Uitgeleend', dot: 'bg-emerald-500' },
  { value: 'defect', label: 'Defect', dot: 'bg-amber-500' },
]

export default function Toolbar({ clusters, filters, setFilters, onBulkAssign, onBulkEnd }) {
  const [filtersOpen, setFiltersOpen] = useState(false)

  const selectClass = "border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-1.5 text-sm bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-School/30 focus:border-School outline-none"

  return (
    <div className="border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-2.5">
      <div className="flex flex-wrap gap-2 items-center">
        {/* Cluster */}
        <select className={selectClass} value={filters.cluster_id || ''}
          onChange={e => setFilters(f => ({ ...f, cluster_id: e.target.value || null }))}>
          <option value="">Alle clusters</option>
          {clusters.map(c => <option key={c.id} value={c.id}>{c.naam}</option>)}
        </select>

        {/* Search */}
        <div className="flex-1 min-w-[200px] relative">
          <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            className="w-full border border-slate-300 dark:border-slate-600 rounded-lg pl-8 pr-3 py-1.5 text-sm dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-School/30 focus:border-School outline-none"
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
            className="bg-School text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-School-600 transition-colors">
            Collectief toekennen
          </button>
        )}
        {onBulkEnd && (
          <button onClick={onBulkEnd}
            className="border-2 border-red-400 text-red-600 dark:text-red-400 px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
            Collectief beëindigen
          </button>
        )}
      </div>
    </div>
  )
}
