import { useState, useEffect } from 'react'
import { api } from '../api'

function RapportDropdown({ vestigingen }) {
  const [open, setOpen] = useState(false)

  function download(type, vestigingId) {
    const params = new URLSearchParams({ type })
    if (vestigingId) params.set('vestiging_id', vestigingId)
    window.open(`/api/dashboard/rapport?${params}`, '_blank')
    setOpen(false)
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="bg-primary text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-primary-600 flex items-center gap-2"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Rapport downloaden
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 mt-2 z-20 bg-white border border-slate-200 rounded-xl shadow-lg py-2 w-72">
            <div className="px-4 py-2 text-xs font-bold text-slate-400 uppercase tracking-wider">Alle vestigingen</div>
            <button onClick={() => download('toewijzingen')} className="w-full text-left px-4 py-2.5 text-sm hover:bg-slate-50 transition-colors">Actieve toewijzingen</button>
            <button onClick={() => download('sleutels')} className="w-full text-left px-4 py-2.5 text-sm hover:bg-slate-50 transition-colors">Openstaande sleutels</button>
            <button onClick={() => download('borg')} className="w-full text-left px-4 py-2.5 text-sm hover:bg-slate-50 transition-colors">Openstaande borg</button>
            {vestigingen.length > 1 && (
              <>
                <div className="border-t my-2" />
                <div className="px-4 py-2 text-xs font-bold text-slate-400 uppercase tracking-wider">Per vestiging</div>
                {vestigingen.map(v => (
                  <div key={v.vestiging_id} className="px-4 py-2">
                    <div className="text-sm font-semibold text-slate-700 mb-1">{v.vestiging_naam}</div>
                    <div className="flex gap-3">
                      <button onClick={() => download('toewijzingen', v.vestiging_id)} className="text-sm text-blue-600 hover:underline">Toewijzingen</button>
                      <button onClick={() => download('sleutels', v.vestiging_id)} className="text-sm text-blue-600 hover:underline">Sleutels</button>
                      <button onClick={() => download('borg', v.vestiging_id)} className="text-sm text-blue-600 hover:underline">Borg</button>
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

function VestigingCard({ s }) {
  const bezetting = s.totaal > 0 ? Math.round((s.uitgeleend / s.totaal) * 100) : 0

  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="px-6 pt-5 pb-4 border-b border-slate-100">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl font-bold text-navy dark:text-white">{s.vestiging_naam}</h2>
          <span className="text-sm text-slate-400">{s.totaal} kluisjes</span>
        </div>
        {/* Bezettingsbalk */}
        <div className="flex items-center gap-3">
          <div className="flex-1 bg-slate-100 rounded-full h-3 overflow-hidden">
            <div className="h-full bg-green-500 rounded-full transition-all" style={{ width: `${bezetting}%` }} />
          </div>
          <span className="text-sm font-semibold text-slate-600">{bezetting}% bezet</span>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4">
        {/* Uitgeleend */}
        <div className="px-6 py-5 border-b lg:border-b-0 lg:border-r border-slate-100">
          <div className="text-3xl font-bold text-green-600">{s.uitgeleend}</div>
          <div className="text-sm text-slate-500 mt-1">Uitgeleend</div>
        </div>
        {/* Vrij */}
        <div className="px-6 py-5 border-b lg:border-b-0 lg:border-r border-slate-100">
          <div className="text-3xl font-bold text-blue-500">{s.vrij}</div>
          <div className="text-sm text-slate-500 mt-1">Vrij</div>
        </div>
        {/* Defect */}
        <div className="px-6 py-5 lg:border-r border-slate-100">
          <div className={`text-3xl font-bold ${s.defect > 0 ? 'text-amber-500' : 'text-slate-300'}`}>{s.defect}</div>
          <div className="text-sm text-slate-500 mt-1">Defect</div>
        </div>
        {/* Sleutel niet ingeleverd */}
        <div className="px-6 py-5">
          <div className={`text-3xl font-bold ${s.sleutel_niet_ingeleverd > 0 ? 'text-red-600' : 'text-slate-300'}`}>{s.sleutel_niet_ingeleverd}</div>
          <div className="text-sm text-slate-500 mt-1">Sleutel niet ingeleverd</div>
        </div>
      </div>

      {/* Borg sectie */}
      {(s.borg_ontvangen > 0 || s.borg_niet_betaald > 0 || s.borg_niet_terug > 0) && (
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-100">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Borg overzicht</div>
          <div className="flex flex-wrap gap-6">
            <div>
              <div className="text-xl font-bold text-slate-700">€{s.borg_ontvangen.toFixed(0)}</div>
              <div className="text-sm text-slate-500">Ontvangen</div>
            </div>
            {s.borg_niet_betaald > 0 && (
              <div>
                <div className="text-xl font-bold text-amber-600">{s.borg_niet_betaald}x</div>
                <div className="text-sm text-slate-500">Niet betaald</div>
              </div>
            )}
            {s.borg_niet_terug > 0 && (
              <div>
                <div className="text-xl font-bold text-red-600">{s.borg_niet_terug}x</div>
                <div className="text-sm text-slate-500">Niet teruggestort</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/api/dashboard/stats')
      .then(setStats)
      .catch(() => setStats([]))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-8 text-lg text-slate-500">Laden...</div>

  // Totals
  const t = stats.reduce((acc, s) => ({
    totaal: acc.totaal + s.totaal,
    uitgeleend: acc.uitgeleend + s.uitgeleend,
    vrij: acc.vrij + s.vrij,
    defect: acc.defect + s.defect,
    sleutel: acc.sleutel + s.sleutel_niet_ingeleverd,
  }), { totaal: 0, uitgeleend: 0, vrij: 0, defect: 0, sleutel: 0 })

  return (
    <div className="p-6 sm:p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-navy">Dashboard</h1>
          {stats.length > 0 && (
            <p className="text-slate-500 mt-1">
              {t.totaal} kluisjes totaal, {t.uitgeleend} uitgeleend
              {t.sleutel > 0 && <span className="text-red-600 font-medium"> — {t.sleutel} sleutel(s) niet ingeleverd</span>}
            </p>
          )}
        </div>
        {stats.length > 0 && <RapportDropdown vestigingen={stats} />}
      </div>

      {stats.length === 0 && (
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-12 text-center">
          <img src="/img/locker-illustration.svg" alt="" className="w-48 mx-auto mb-6 opacity-60" />
          <p className="text-lg text-slate-500">Geen vestigingen gevonden.</p>
          <p className="text-sm text-slate-400 mt-1">Maak eerst een vestiging aan via Beheer.</p>
        </div>
      )}

      {/* Per vestiging */}
      {stats.map(s => <VestigingCard key={s.vestiging_id} s={s} />)}
    </div>
  )
}
