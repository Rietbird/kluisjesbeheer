import { useState } from 'react'

export default function Toolbar({ vestigingen, clusters, filters, setFilters, onBulkAssign }) {
  const [filtersOpen, setFiltersOpen] = useState(false)

  return (
    <div className="border-b border-slate-200 bg-white">
      <div className="p-2 flex flex-wrap gap-2 items-center">
        <select className="border rounded px-2 py-1 text-sm" value={filters.vestiging_id || ''}
          onChange={e => setFilters(f => ({ ...f, vestiging_id: e.target.value || null, cluster_id: null }))}>
          <option value="">Vestiging...</option>
          {vestigingen.map(v => <option key={v.id} value={v.id}>{v.naam}</option>)}
        </select>
        <select className="border rounded px-2 py-1 text-sm" value={filters.cluster_id || ''}
          onChange={e => setFilters(f => ({ ...f, cluster_id: e.target.value || null }))}>
          <option value="">Alle clusters</option>
          {clusters.map(c => <option key={c.id} value={c.id}>{c.naam}</option>)}
        </select>
        <div className="flex-1 min-w-[180px]">
          <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Zoek kluisnr, naam, stamnr..."
            value={filters.q} onChange={e => setFilters(f => ({ ...f, q: e.target.value }))} />
        </div>
        <button className="md:hidden border rounded px-2 py-1 text-sm text-slate-500"
          onClick={() => setFiltersOpen(!filtersOpen)}>Filters</button>
        <div className={`${filtersOpen ? 'flex' : 'hidden'} md:flex gap-1`}>
          {['', 'vrij', 'uitgeleend', 'defect'].map(s => (
            <button key={s} onClick={() => setFilters(f => ({ ...f, status: s }))}
              className={`px-2 py-1 text-xs rounded border ${filters.status === s ? 'bg-navy text-white' : 'text-slate-500'}`}>
              {s || 'Alles'}
            </button>
          ))}
        </div>
        <div className="flex border rounded overflow-hidden">
          <button onClick={() => setFilters(f => ({ ...f, view: 'table' }))}
            className={`px-2 py-1 text-xs ${filters.view === 'table' ? 'bg-navy text-white' : 'text-slate-500'}`}>☰</button>
          <button onClick={() => setFilters(f => ({ ...f, view: 'grid' }))}
            className={`px-2 py-1 text-xs ${filters.view === 'grid' ? 'bg-navy text-white' : 'text-slate-500'}`}>⊞</button>
        </div>
        {onBulkAssign && (
          <button onClick={onBulkAssign}
            className="bg-navy text-white px-3 py-1 rounded text-sm hover:bg-navy/90">Collectief toekennen</button>
        )}
      </div>
    </div>
  )
}
