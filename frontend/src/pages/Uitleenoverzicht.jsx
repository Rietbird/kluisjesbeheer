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


function VestigingPicker({ vestigingen, onSelect, onSelectWithFilter }) {
  const [stats, setStats] = useState([])
  const { borgActiefVoor, kleurVoor } = useInstellingen()

  useEffect(() => {
    api.get('/api/dashboard/stats').then(setStats).catch(() => {})
  }, [])

  const getStats = (vid) => stats.find(s => s.vestiging_id === vid) || {}

  // Totals
  const t = stats.reduce((a, s) => ({
    totaal: a.totaal + (s.totaal || 0),
    uitgeleend: a.uitgeleend + (s.uitgeleend || 0),
    sleutel: a.sleutel + (s.sleutel_niet_ingeleverd || 0),
  }), { totaal: 0, uitgeleend: 0, sleutel: 0 })

  return (
    <div className="p-6 sm:p-8 max-w-5xl mx-auto">
      {/* Vestiging kaarten */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-10">
        {vestigingen.map((v, i) => {
          const s = getStats(v.id)
          const bezetting = s.totaal > 0 ? Math.round((s.uitgeleend || 0) / s.totaal * 100) : 0
          const kleur = kleurVoor(v.id, i)
          return (
            <div key={v.id}
              className="group text-left bg-white dark:bg-slate-800 border-2 border-slate-200 dark:border-slate-700 rounded-2xl overflow-hidden hover:shadow-xl transition-all flex cursor-pointer"
              style={{ '--vestiging-kleur': kleur }}
              onClick={() => onSelect(v.id)}>
              <div className="w-1.5 shrink-0" style={{ backgroundColor: kleur }} />
              <div className="p-5 flex-1">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-11 h-11 rounded-xl flex items-center justify-center text-white font-bold text-lg group-hover:scale-110 transition-transform"
                    style={{ backgroundColor: kleur }}>
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
                    <div onClick={e => { e.stopPropagation(); onSelectWithFilter(v.id, 'uitgeleend') }} className="cursor-pointer hover:opacity-70 transition-opacity">
                      <div className="text-xl font-bold text-emerald-600">{s.uitgeleend || 0}</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">Uitgeleend</div>
                    </div>
                    <div onClick={e => { e.stopPropagation(); onSelectWithFilter(v.id, 'vrij') }} className="cursor-pointer hover:opacity-70 transition-opacity">
                      <div className="text-xl font-bold text-sky-500">{s.vrij || 0}</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">Vrij</div>
                    </div>
                    <div onClick={e => { e.stopPropagation(); if ((s.defect || 0) > 0) onSelectWithFilter(v.id, 'defect') }}
                      className={`${(s.defect || 0) > 0 ? 'cursor-pointer hover:opacity-70' : ''} transition-opacity`}>
                      <div className={`text-xl font-bold ${(s.defect || 0) > 0 ? 'text-amber-500' : 'text-slate-300 dark:text-slate-600'}`}>{s.defect || 0}</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">Defect</div>
                    </div>
                    <div onClick={e => { e.stopPropagation(); if ((s.sleutel_niet_ingeleverd || 0) > 0) onSelectWithFilter(v.id, 'vrij') }}
                      className={`${(s.sleutel_niet_ingeleverd || 0) > 0 ? 'cursor-pointer hover:opacity-70' : ''} transition-opacity`}>
                      <div className={`text-xl font-bold ${(s.sleutel_niet_ingeleverd || 0) > 0 ? 'text-red-600' : 'text-slate-300 dark:text-slate-600'}`}>{s.sleutel_niet_ingeleverd || 0}</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">Sleutel niet ingeleverd</div>
                    </div>
                  </div>
                )}

                {/* Bezettingsbalk */}
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
                {borgActiefVoor(v.id) && (s.borg_ontvangen > 0 || s.borg_niet_betaald > 0 || s.borg_niet_terug > 0) && (
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
            </div>
          )
        })}
      </div>

      {/* Illustration + title below cards */}
      <div className="text-center">
        <img src="/img/locker-illustration.svg" alt="" className="w-44 mx-auto mb-5 opacity-60" />
        {stats.length > 0 ? (
          <>
            <h2 className="text-2xl font-bold text-navy dark:text-white">Kies een vestiging</h2>
            <p className="text-slate-500 dark:text-slate-400 mt-1">
              {t.totaal} kluisjes totaal, {t.uitgeleend} uitgeleend{t.sleutel > 0 && <span className="text-red-600 dark:text-red-400 font-medium"> — {t.sleutel} sleutel(s) niet ingeleverd</span>}
            </p>
          </>
        ) : (
          <>
            <h2 className="text-2xl font-bold text-navy dark:text-white">Welkom bij Kluisjesbeheer</h2>
            <p className="text-slate-500 dark:text-slate-400 mt-1 max-w-md mx-auto">
              Er zijn nog geen vestigingen of kluisjes aangemaakt. Ga naar <strong>Beheer</strong> om vestigingen en clusters aan te maken, of importeer kluisjes via een Excel-bestand.
            </p>
          </>
        )}
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
              ? 'text-primary bg-slate-50 dark:bg-slate-900 border-t-2 border-x border-primary border-x-slate-200 dark:border-x-slate-700 -mb-px'
              : 'text-slate-500 dark:text-slate-400 hover:text-primary hover:bg-slate-50 dark:hover:bg-slate-700'
          }`}>
          {v.naam}
        </button>
      ))}
      {/* Back to overview */}
      <button onClick={() => onChange(null)}
        className="ml-auto px-3 py-2 text-xs text-slate-400 hover:text-primary transition-colors flex items-center gap-1">
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
            onBulkEnd={() => setShowBulkEnd(true)}
            vestigingId={filters.vestiging_id} />
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
