import { useState } from 'react'
import { useKluisjes } from '../hooks/useKluisjes'
import Toolbar from '../components/Toolbar'
import LockerGrid from '../components/LockerGrid'
import LockerTable from '../components/LockerTable'
import SidePanel from '../components/SidePanel'
import BulkWizard from '../components/BulkWizard'

export default function Uitleenoverzicht() {
  const { vestigingen, clusters, kluisjes, loading, filters, setFilters, reload } = useKluisjes()
  const [selected, setSelected] = useState(null)
  const [showBulk, setShowBulk] = useState(false)

  const filtered = filters.cluster_id
    ? kluisjes.filter(k => k.cluster_id === Number(filters.cluster_id))
    : kluisjes

  return (
    <div className="flex h-[calc(100vh-44px)]">
      <div className="flex-1 flex flex-col min-w-0">
        <Toolbar vestigingen={vestigingen} clusters={clusters} filters={filters} setFilters={setFilters}
          onBulkAssign={filters.vestiging_id ? () => setShowBulk(true) : null} />
        <div className="flex-1 overflow-auto p-4">
          {loading && <p className="text-slate-500">Laden...</p>}
          {!loading && !filters.vestiging_id && <p className="text-slate-500">Kies een vestiging om kluisjes te zien.</p>}
          {!loading && filters.vestiging_id && filtered.length === 0 && <p className="text-slate-500">Geen kluisjes gevonden.</p>}
          {!loading && filtered.length > 0 && (
            filters.view === 'grid'
              ? <LockerGrid kluisjes={filtered} onSelect={setSelected} selectedId={selected?.id} />
              : <LockerTable kluisjes={filtered} onSelect={setSelected} selectedId={selected?.id} />
          )}
        </div>
      </div>
      {selected && (
        <SidePanel kluisje={selected} onClose={() => setSelected(null)} onUpdate={() => { reload(); setSelected(null) }} />
      )}
      {showBulk && (
        <BulkWizard vestigingId={filters.vestiging_id} onClose={() => setShowBulk(false)} onDone={() => { setShowBulk(false); reload() }} />
      )}
    </div>
  )
}
