import { useState, useEffect } from 'react'
import { useKluisjes } from '../hooks/useKluisjes'
import { useInstellingen } from '../context/InstellingenContext'
import { api } from '../api'
import Toolbar from '../components/Toolbar'
import LockerGrid from '../components/LockerGrid'
import LockerTable from '../components/LockerTable'
import LockerModal from '../components/LockerModal'
import BulkWizard from '../components/BulkWizard'
import BulkEndWizard from '../components/BulkEndWizard'

function RapportDropdown({ stats }) {
  const [open, setOpen] = useState(false)
  const { borgActief } = useInstellingen()

  function download(type, vestigingId) {
    const params = new URLSearchParams({ type })
    if (vestigingId) params.set('vestiging_id', vestigingId)
    window.open(`/api/dashboard/rapport?${params}`, '_blank')
    setOpen(false)
  }

  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)}
        className="bg-School text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-School-600 flex items-center gap-2 transition-colors">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Rapport
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 mt-2 z-20 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-lg py-2 w-64">
            <div className="px-4 py-1.5 text-xs font-bold text-slate-400 uppercase tracking-wider">Alle vestigingen</div>
            <button onClick={() => download('toewijzingen')} className="w-full text-left px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700">Actieve toewijzingen</button>
            <button onClick={() => download('sleutels')} className="w-full text-left px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700">Openstaande sleutels</button>
            {borgActief && <button onClick={() => download('borg')} className="w-full text-left px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700">Openstaande borg</button>}
            {stats.length > 1 && (
              <>
                <div className="border-t dark:border-slate-700 my-1" />
                <div className="px-4 py-1.5 text-xs font-bold text-slate-400 uppercase tracking-wider">Per vestiging</div>
                {stats.map(v => (
                  <div key={v.vestiging_id} className="px-4 py-1.5">
                    <div className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-0.5">{v.vestiging_naam}</div>
                    <div className="flex gap-3">
                      <button onClick={() => download('toewijzingen', v.vestiging_id)} className="text-xs text-School hover:underline">Toewijzingen</button>
                      <button onClick={() => download('sleutels', v.vestiging_id)} className="text-xs text-School hover:underline">Sleutels</button>
                      {borgActief && <button onClick={() => download('borg', v.vestiging_id)} className="text-xs text-School hover:underline">Borg</button>}
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        </>
      )}
    </div>
  )
}

function VestigingPicker({ vestigingen, onSelect }) {
  const [stats, setStats] = useState([])

  useEffect(() => {
    api.get('/api/dashboard/stats').then(setStats).catch(() => {})
  }, [])

  const getStats = (vid) => stats.find(s => s.vestiging_id === vid) || {}
  const colors = ['from-teal-400 to-emerald-500', 'from-blue-500 to-indigo-500', 'from-violet-500 to-purple-500', 'from-School to-amber-500']

  // Totals
  const t = stats.reduce((a, s) => ({
    totaal: a.totaal + (s.totaal || 0),
    uitgeleend: a.uitgeleend + (s.uitgeleend || 0),
    sleutel: a.sleutel + (s.sleutel_niet_ingeleverd || 0),
  }), { totaal: 0, uitgeleend: 0, sleutel: 0 })

  return (
    <div className="p-6 sm:p-8 max-w-5xl mx-auto">
      {/* Rapport knop */}
      {stats.length > 0 && (
        <div className="flex justify-end mb-4">
          <RapportDropdown stats={stats} />
        </div>
      )}

      {/* Vestiging kaarten */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-10">
        {vestigingen.map((v, i) => {
          const s = getStats(v.id)
          const bezetting = s.totaal > 0 ? Math.round((s.uitgeleend || 0) / s.totaal * 100) : 0
          return (
            <button key={v.id} onClick={() => onSelect(v.id)}
              className="group text-left bg-white dark:bg-slate-800 border-2 border-slate-200 dark:border-slate-700 rounded-2xl overflow-hidden hover:border-School dark:hover:border-School hover:shadow-xl transition-all flex">
              <div className={`w-1.5 bg-gradient-to-b ${colors[i % colors.length]} shrink-0`} />
              <div className="p-5 flex-1">
                <div className="flex items-center gap-3 mb-4">
                  <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${colors[i % colors.length]} flex items-center justify-center text-white font-bold text-lg group-hover:scale-110 transition-transform`}>
                    {v.naam[0]}
                  </div>
                  <div>
                    <div className="text-lg font-bold text-navy dark:text-white">{v.naam}</div>
                    <div className="text-sm text-slate-500 dark:text-slate-400">{s.totaal || 0} kluisjes</div>
                  </div>
                </div>

                {/* Stats row */}
                {s.totaal != null && (
                  <div className="grid grid-cols-4 gap-2 mb-3">
                    <div>
                      <div className="text-xl font-bold text-emerald-600">{s.uitgeleend || 0}</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">Uitgeleend</div>
                    </div>
                    <div>
                      <div className="text-xl font-bold text-sky-500">{s.vrij || 0}</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">Vrij</div>
                    </div>
                    <div>
                      <div className={`text-xl font-bold ${(s.defect || 0) > 0 ? 'text-amber-500' : 'text-slate-300 dark:text-slate-600'}`}>{s.defect || 0}</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">Defect</div>
                    </div>
                    <div>
                      <div className={`text-xl font-bold ${(s.sleutel_niet_ingeleverd || 0) > 0 ? 'text-red-600' : 'text-slate-300 dark:text-slate-600'}`}>{s.sleutel_niet_ingeleverd || 0}</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">Sleutel niet ingeleverd</div>
                    </div>
                  </div>
                )}

                {/* Bezettingsbalk - only show bar when bezetting > 0 */}
                {s.totaal > 0 && (
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-slate-100 dark:bg-slate-700 rounded-full h-2 overflow-hidden">
                      {bezetting > 0 && (
                        <div className="h-full bg-emerald-500 transition-all" style={{ width: `${bezetting}%` }} />
                      )}
                    </div>
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 w-10 text-right">{bezetting}%</span>
                  </div>
                )}

                {/* Borg info */}
                {borgActief && (s.borg_ontvangen > 0 || s.borg_niet_betaald > 0 || s.borg_niet_terug > 0) && (
                  <div className="flex gap-4 mt-3 pt-3 border-t border-slate-100 dark:border-slate-700 text-xs">
                    {s.borg_ontvangen > 0 && (
                      <span className="text-slate-600 dark:text-slate-400">Borg: <span className="font-semibold">€{s.borg_ontvangen.toFixed(0)}</span></span>
                    )}
                    {s.borg_niet_betaald > 0 && (
                      <span className="text-amber-600">{s.borg_niet_betaald}x borg niet betaald</span>
                    )}
                    {s.borg_niet_terug > 0 && (
                      <span className="text-red-600">{s.borg_niet_terug}x borg niet teruggestort</span>
                    )}
                  </div>
                )}
              </div>
            </button>
          )
        })}
      </div>

      {/* Illustration + title below cards */}
      <div className="text-center">
        <img src="/img/locker-illustration.svg" alt="" className="w-44 mx-auto mb-5 opacity-60" />
        <h2 className="text-2xl font-bold text-navy dark:text-white">Kies een vestiging</h2>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          {stats.length > 0
            ? <>{t.totaal} kluisjes totaal, {t.uitgeleend} uitgeleend{t.sleutel > 0 && <span className="text-red-600 dark:text-red-400 font-medium"> — {t.sleutel} sleutel(s) niet ingeleverd</span>}</>
            : 'Selecteer een vestiging om de kluisjes te beheren'
          }
        </p>
      </div>
    </div>
  )
}

function VestigingTabs({ vestigingen, activeId, onChange }) {
  return (
    <div className="flex gap-1 px-4 pt-2 pb-0 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 overflow-x-auto">
      {vestigingen.map(v => (
        <button key={v.id} onClick={() => onChange(v.id)}
          className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors whitespace-nowrap ${
            activeId === String(v.id)
              ? 'text-School bg-slate-50 dark:bg-slate-900 border-t-2 border-x border-School border-x-slate-200 dark:border-x-slate-700 -mb-px'
              : 'text-slate-500 dark:text-slate-400 hover:text-School hover:bg-slate-50 dark:hover:bg-slate-700'
          }`}>
          {v.naam}
        </button>
      ))}
      {/* Back to overview */}
      <button onClick={() => onChange(null)}
        className="ml-auto px-3 py-2 text-xs text-slate-400 hover:text-School transition-colors flex items-center gap-1">
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
        </svg>
        Overzicht
      </button>
    </div>
  )
}

export default function Uitleenoverzicht() {
  const { vestigingen, clusters, kluisjes, loading, filters, setFilters, reload } = useKluisjes()
  const { borgActief } = useInstellingen()
  const [selected, setSelected] = useState(null)
  const [showBulk, setShowBulk] = useState(false)
  const [showBulkEnd, setShowBulkEnd] = useState(false)

  const filtered = filters.cluster_id
    ? kluisjes.filter(k => k.cluster_id === Number(filters.cluster_id))
    : kluisjes

  const hasVestiging = !!filters.vestiging_id

  function selectVestiging(id) {
    if (id === null) {
      setFilters(f => ({ ...f, vestiging_id: null, cluster_id: null }))
    } else {
      setFilters(f => ({ ...f, vestiging_id: String(id), cluster_id: null }))
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-52px)]">
      {!hasVestiging && (
        <div className="flex-1 overflow-auto">
          <VestigingPicker vestigingen={vestigingen} onSelect={selectVestiging} />
        </div>
      )}

      {hasVestiging && (
        <>
          <VestigingTabs vestigingen={vestigingen} activeId={filters.vestiging_id} onChange={selectVestiging} />
          <Toolbar clusters={clusters} filters={filters} setFilters={setFilters}
            onBulkAssign={() => setShowBulk(true)}
            onBulkEnd={() => setShowBulkEnd(true)} />
          <div className="flex-1 overflow-auto p-5 bg-slate-50 dark:bg-slate-900">
            {loading && <p className="text-slate-500 text-lg">Laden...</p>}
            {!loading && filtered.length === 0 && (
              <p className="text-slate-400 dark:text-slate-500 text-lg">Geen kluisjes gevonden.</p>
            )}
            {!loading && filtered.length > 0 && (
              filters.view === 'grid'
                ? <LockerGrid kluisjes={filtered} onSelect={setSelected} selectedId={selected?.id} />
                : <LockerTable kluisjes={filtered} onSelect={setSelected} selectedId={selected?.id} />
            )}
          </div>
        </>
      )}

      {selected && (
        <LockerModal kluisje={selected} onClose={() => setSelected(null)} onUpdate={() => { reload(); setSelected(null) }} />
      )}
      {showBulk && (
        <BulkWizard vestigingId={filters.vestiging_id} onClose={() => setShowBulk(false)} onDone={() => { setShowBulk(false); reload() }} />
      )}
      {showBulkEnd && (
        <BulkEndWizard vestigingId={filters.vestiging_id} onClose={() => setShowBulkEnd(false)} onDone={() => { setShowBulkEnd(false); reload() }} />
      )}
    </div>
  )
}
