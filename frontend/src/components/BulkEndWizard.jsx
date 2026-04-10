import { useState, useEffect, useMemo } from 'react'
import { api } from '../api'
import { useInstellingen } from '../context/InstellingenContext'
import { formatDate } from '../utils/formatDate'

const steps = ['Selectie', 'Opties', 'Bevestigen']

export default function BulkEndWizard({ vestigingId, onClose, onDone }) {
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(true)
  const [toewijzingen, setToewijzingen] = useState([])
  const [clusters, setClusters] = useState([])
  const [clusterId, setClusterId] = useState('')
  const [klasFilter, setKlasFilter] = useState('')
  const [selected, setSelected] = useState(new Set())
  const [sleutelMap, setSleutelMap] = useState({}) // { [toewijzing_id]: boolean }
  const [borgTeruggestort, setBorgTeruggestort] = useState(false)
  const [einddatum, setEinddatum] = useState(new Date().toISOString().slice(0, 10))
  const [opmerking, setOpmerking] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)
  const { borgActiefVoor } = useInstellingen()

  useEffect(() => {
    api.get(`/api/vestigingen/${vestigingId}/clusters`).then(setClusters).catch(() => {})
  }, [vestigingId])

  useEffect(() => {
    setLoading(true)
    const params = new URLSearchParams({ vestiging_id: vestigingId })
    if (clusterId) params.set('cluster_id', clusterId)
    api.get(`/api/toewijzingen/actief?${params}`)
      .then(data => { setToewijzingen(data); setSelected(new Set()) })
      .catch(() => setToewijzingen([]))
      .finally(() => setLoading(false))
  }, [vestigingId, clusterId])

  const klassen = useMemo(() => {
    const set = new Set(toewijzingen.map(t => t.leerling_klas).filter(Boolean))
    return [...set].sort()
  }, [toewijzingen])

  const filtered = useMemo(() => {
    const list = klasFilter
      ? toewijzingen.filter(t => t.leerling_klas === klasFilter)
      : toewijzingen
    return [...list].sort((a, b) => (a.leerling_naam || '').localeCompare(b.leerling_naam || '', 'nl'))
  }, [toewijzingen, klasFilter])

  function toggleAll() {
    if (selected.size === filtered.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(filtered.map(t => t.id)))
    }
  }

  function toggle(id) {
    const next = new Set(selected)
    next.has(id) ? next.delete(id) : next.add(id)
    setSelected(next)
  }

  // When moving to step 1, initialize sleutelMap for all selected toewijzingen (default: true)
  function goToStep1() {
    const map = {}
    for (const id of selected) {
      map[id] = sleutelMap[id] !== undefined ? sleutelMap[id] : true
    }
    setSleutelMap(map)
    setStep(1)
  }

  function toggleSleutel(id) {
    setSleutelMap(prev => ({ ...prev, [id]: !prev[id] }))
  }

  async function handleSubmit() {
    setSubmitting(true)
    try {
      const res = await api.post('/api/toewijzingen/bulk-beeindigen', {
        toewijzing_ids: [...selected],
        sleutel_map: Object.fromEntries(Object.entries(sleutelMap).map(([k, v]) => [k, v])),
        borg_teruggestort: borgTeruggestort,
        einddatum,
        opmerking,
      })
      setResult(res)
      setStep(3)
    } catch (err) {
      alert(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const selectedList = useMemo(() =>
    filtered.filter(t => selected.has(t.id)),
    [filtered, selected]
  )

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden">

        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-red-50 to-white dark:from-slate-800 dark:to-slate-800">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-navy dark:text-white">Collectief beëindigen</h2>
            <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          {/* Steps */}
          {step < 3 && (
            <div className="flex gap-2 mt-3">
              {steps.map((s, i) => (
                <div key={i} className={`flex items-center gap-1.5 text-xs font-medium ${i <= step ? 'text-primary' : 'text-slate-400'}`}>
                  <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${
                    i < step ? 'bg-primary text-white' : i === step ? 'bg-primary text-white' : 'bg-slate-200 dark:bg-slate-600 text-slate-500'
                  }`}>{i < step ? '✓' : i + 1}</span>
                  {s}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">

          {/* Step 0: Selectie — gesorteerd op leerling_naam */}
          {step === 0 && (
            <div className="space-y-4">
              <div className="flex gap-3">
                <select className="border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-700 dark:text-white"
                  value={clusterId} onChange={e => setClusterId(e.target.value)}>
                  <option value="">Alle clusters</option>
                  {clusters.map(c => <option key={c.id} value={c.id}>{c.naam}</option>)}
                </select>
                <select className="border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-700 dark:text-white"
                  value={klasFilter} onChange={e => setKlasFilter(e.target.value)}>
                  <option value="">Alle klassen</option>
                  {klassen.map(k => <option key={k} value={k}>{k}</option>)}
                </select>
              </div>

              {loading ? (
                <p className="text-slate-500">Laden...</p>
              ) : filtered.length === 0 ? (
                <p className="text-slate-400">Geen actieve toewijzingen gevonden.</p>
              ) : (
                <>
                  <div className="flex items-center justify-between">
                    <label className="flex items-center gap-2 text-sm cursor-pointer">
                      <input type="checkbox" className="w-4 h-4 accent-primary"
                        checked={selected.size === filtered.length && filtered.length > 0}
                        onChange={toggleAll} />
                      <span className="font-medium">Alles selecteren ({filtered.length})</span>
                    </label>
                    <span className="text-sm text-primary font-semibold">{selected.size} geselecteerd</span>
                  </div>
                  <div className="max-h-72 overflow-y-auto border border-slate-200 dark:border-slate-600 rounded-xl divide-y divide-slate-100 dark:divide-slate-700">
                    {filtered.map(t => (
                      <label key={t.id} className="flex items-center gap-3 px-4 py-2.5 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer transition-colors">
                        <input type="checkbox" className="w-4 h-4 accent-primary"
                          checked={selected.has(t.id)} onChange={() => toggle(t.id)} />
                        <span className="text-sm flex-1">{t.leerling_naam}</span>
                        <span className="text-xs text-slate-500 w-16">{t.leerling_klas}</span>
                        <span className="font-medium text-sm text-navy dark:text-white w-20 text-right">{t.kluisnummer}</span>
                      </label>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {/* Step 1: Opties */}
          {step === 1 && (
            <div className="space-y-5">
              <p className="text-sm text-slate-600 dark:text-slate-300">
                Stel de opties in voor het beëindigen van <strong>{selected.size} toewijzing(en)</strong>.
              </p>
              {borgActiefVoor(vestigingId) && (
                <label className="flex items-center gap-3 p-4 border border-slate-200 dark:border-slate-600 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer transition-colors">
                  <input type="checkbox" className="w-5 h-5 accent-primary"
                    checked={borgTeruggestort} onChange={e => setBorgTeruggestort(e.target.checked)} />
                  <div>
                    <div className="font-medium text-sm">Borg teruggestort</div>
                    <div className="text-xs text-slate-500">Markeer de borg als teruggestort voor alle geselecteerde leerlingen</div>
                  </div>
                </label>
              )}
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Einddatum</label>
                <input type="date" className="border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2.5 text-sm w-full bg-white dark:bg-slate-700 dark:text-white"
                  value={einddatum} onChange={e => setEinddatum(e.target.value)} />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Opmerking (optioneel)</label>
                <textarea className="border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2.5 text-sm w-full resize-none bg-white dark:bg-slate-700 dark:text-white"
                  rows={2} value={opmerking} onChange={e => setOpmerking(e.target.value)}
                  placeholder="Bijv. 'Einde schooljaar 2025-2026'" />
              </div>
            </div>
          )}

          {/* Step 2: Bevestigen — per leerling sleutel ingeleverd */}
          {step === 2 && (
            <div className="space-y-4">
              <div className="bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-700 rounded-xl p-4">
                <div className="font-semibold text-amber-800 dark:text-amber-300">Let op</div>
                <div className="text-sm text-amber-700 dark:text-amber-400 mt-1">
                  Je staat op het punt om <strong>{selected.size} toewijzing(en)</strong> te beëindigen. Dit kan niet ongedaan worden gemaakt.
                </div>
              </div>
              <div className="text-sm space-y-1">
                <div className="flex justify-between py-1"><span className="text-slate-500">Aantal</span><span className="font-semibold">{selected.size} kluisjes</span></div>
                {borgActiefVoor(vestigingId) && <div className="flex justify-between py-1"><span className="text-slate-500">Borg teruggestort</span><span className="font-semibold">{borgTeruggestort ? 'Ja' : 'Nee'}</span></div>}
                <div className="flex justify-between py-1"><span className="text-slate-500">Einddatum</span><span className="font-semibold">{formatDate(einddatum)}</span></div>
                {opmerking && <div className="flex justify-between py-1"><span className="text-slate-500">Opmerking</span><span className="font-semibold">{opmerking}</span></div>}
              </div>
              <div className="overflow-x-auto border border-slate-200 dark:border-slate-600 rounded-xl max-h-64 overflow-y-auto">
                <table className="w-full text-xs">
                  <thead className="sticky top-0">
                    <tr className="bg-slate-50 dark:bg-slate-700 text-slate-500">
                      <th className="px-3 py-2 text-left font-medium">Naam</th>
                      <th className="px-3 py-2 text-left font-medium">Klas</th>
                      <th className="px-3 py-2 text-left font-medium">Kluisnr</th>
                      <th className="px-3 py-2 text-left font-medium">Sleutelnr</th>
                      <th className="px-3 py-2 text-center font-medium">Sleutel ingeleverd</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                    {selectedList.map(t => (
                      <tr key={t.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                        <td className="px-3 py-2">{t.leerling_naam}</td>
                        <td className="px-3 py-2 text-slate-500">{t.leerling_klas}</td>
                        <td className="px-3 py-2 font-medium">{t.kluisnummer}</td>
                        <td className="px-3 py-2 text-slate-500">{t.sleutelnummer || '—'}</td>
                        <td className="px-3 py-2 text-center">
                          <input
                            type="checkbox"
                            className="w-4 h-4 accent-primary cursor-pointer"
                            checked={!!sleutelMap[t.id]}
                            onChange={() => toggleSleutel(t.id)}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-slate-400">
                {Object.values(sleutelMap).filter(Boolean).length} van {selected.size} sleutels worden als ingeleverd gemarkeerd.
              </p>
            </div>
          )}

          {/* Step 3: Resultaat */}
          {step === 3 && result && (
            <div className="text-center py-8">
              <div className="text-4xl mb-4">✓</div>
              <div className="text-xl font-bold text-emerald-600">{result.ended} toewijzing(en) beëindigd</div>
              <p className="text-sm text-slate-500 mt-2">De kluisjes zijn nu weer vrij.</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 flex justify-between">
          {step < 3 ? (
            <>
              <button onClick={step === 0 ? onClose : () => setStep(step - 1)}
                className="px-5 py-2.5 border border-slate-300 dark:border-slate-600 rounded-lg text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
                {step === 0 ? 'Annuleren' : 'Vorige'}
              </button>
              {step < 2 ? (
                <button
                  onClick={step === 0 ? goToStep1 : () => setStep(step + 1)}
                  disabled={step === 0 && selected.size === 0}
                  className="px-5 py-2.5 bg-primary text-white rounded-lg text-sm font-semibold hover:bg-primary-600 disabled:opacity-40 transition-colors">
                  Volgende
                </button>
              ) : (
                <button onClick={handleSubmit} disabled={submitting}
                  className="px-5 py-2.5 bg-red-600 text-white rounded-lg text-sm font-semibold hover:bg-red-700 disabled:opacity-50 transition-colors">
                  {submitting ? 'Bezig...' : `${selected.size} toewijzingen beëindigen`}
                </button>
              )}
            </>
          ) : (
            <div className="w-full flex justify-end">
              <button onClick={onDone}
                className="px-5 py-2.5 bg-primary text-white rounded-lg text-sm font-semibold hover:bg-primary-600 transition-colors">
                Sluiten
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
