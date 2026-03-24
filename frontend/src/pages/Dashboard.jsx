import { useState, useEffect } from 'react'
import { api } from '../api'
import StatCard from '../components/StatCard'

export default function Dashboard() {
  const [stats, setStats] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/api/dashboard/stats')
      .then(setStats)
      .catch(() => setStats([]))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-4 text-slate-500">Laden...</div>

  return (
    <div className="p-4 max-w-5xl mx-auto">
      <h1 className="text-xl font-bold text-navy mb-4">Dashboard</h1>
      {stats.length === 0 && <p className="text-slate-500">Geen vestigingen gevonden. Maak eerst een vestiging aan via Beheer.</p>}
      {stats.map(s => (
        <div key={s.vestiging_id} className="mb-6">
          <h2 className="text-sm font-semibold text-slate-600 mb-2">{s.vestiging_naam}</h2>
          <div className="flex flex-wrap gap-3">
            <StatCard label="Totaal" value={s.totaal} />
            <StatCard label="Uitgeleend" value={s.uitgeleend} color="text-green-500" />
            <StatCard label="Vrij" value={s.vrij} color="text-blue-500" />
            <StatCard label="Defect" value={s.defect} color="text-red-500" />
            {s.sleutel_niet_ingeleverd > 0 && (
              <StatCard label="Sleutel niet ingeleverd" value={s.sleutel_niet_ingeleverd} color="text-red-600" />
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
