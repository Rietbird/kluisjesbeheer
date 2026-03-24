import { useState, useEffect } from 'react'
import { api } from '../api'

const STEPS = ['Klas', 'Leerlingen', 'Periode & Kluisjes', 'Toekenning', 'Bevestigen']

export default function BulkWizard({ vestigingId, onClose, onDone }) {
  const [step, setStep] = useState(0)
  const [klassen, setKlassen] = useState([])
  const [selectedKlas, setSelectedKlas] = useState('')
  const [leerlingen, setLeerlingen] = useState([])
  const [selectedLeerlingen, setSelectedLeerlingen] = useState([])
  const [leerlingFilter, setLeerlingFilter] = useState('')
  const [periodeVan, setPeriodeVan] = useState('')
  const [periodeTot, setPeriodeTot] = useState('')
  const [vestigingen, setVestigingen] = useState([])
  const [clusters, setClusters] = useState([])
  const [selectedVestiging, setSelectedVestiging] = useState(vestigingId || '')
  const [selectedCluster, setSelectedCluster] = useState('')
  const [availableCount, setAvailableCount] = useState(null)
  const [vrijevKluisjes, setVrijeKluisjes] = useState([])
  const [toekenningWijze, setToekenningWijze] = useState('volgorde')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  useEffect(() => {
    api.get('/api/magister/klassen').then(setKlassen).catch(() => {})
    api.get('/api/vestigingen').then(setVestigingen).catch(() => {})
  }, [])

  useEffect(() => {
    if (selectedVestiging) {
      api.get(`/api/vestigingen/${selectedVestiging}/clusters`).then(setClusters).catch(() => {})
    } else {
      setClusters([])
    }
    setSelectedCluster('')
    setVrijeKluisjes([])
    setAvailableCount(null)
  }, [selectedVestiging])

  useEffect(() => {
    if (selectedCluster) {
      api.get(`/api/clusters/${selectedCluster}/kluisjes`)
        .then(data => {
          const vrij = data.filter(k => k.status === 'vrij')
          setVrijeKluisjes(vrij)
          setAvailableCount(vrij.length)
        })
        .catch(() => { setVrijeKluisjes([]); setAvailableCount(0) })
    } else {
      setVrijeKluisjes([])
      setAvailableCount(null)
    }
  }, [selectedCluster])

  async function loadLeerlingen(klas) {
    setLoading(true)
    try {
      const data = await api.get(`/api/magister/leerlingen?q=${encodeURIComponent(klas)}`)
      setLeerlingen(data)
      setSelectedLeerlingen(data.map((_, i) => i))
    } catch {
      setLeerlingen([])
    } finally {
      setLoading(false)
    }
  }

  function nextStep() {
    setError('')
    if (step === 0) {
      if (!selectedKlas) { setError('Kies een klas.'); return }
      loadLeerlingen(selectedKlas)
      setStep(1)
    } else if (step === 1) {
      if (selectedLeerlingen.length === 0) { setError('Selecteer minimaal één leerling.'); return }
      setStep(2)
    } else if (step === 2) {
      if (!periodeVan || !periodeTot) { setError('Vul de periode in.'); return }
      if (!selectedCluster) { setError('Kies een cluster.'); return }
      const needed = selectedLeerlingen.length
      if (availableCount !== null && availableCount < needed) {
        setError(`Niet genoeg vrije kluisjes. Nodig: ${needed}, beschikbaar: ${availableCount}.`)
        return
      }
      setStep(3)
    } else if (step === 3) {
      setStep(4)
    }
  }

  function prevStep() {
    setError('')
    setStep(s => Math.max(0, s - 1))
  }

  async function handleSubmit() {
    setLoading(true)
    setError('')
    try {
      const leerlingenList = selectedLeerlingen.map(i => leerlingen[i])
      let kluisjesList = [...vrijevKluisjes]
      if (toekenningWijze === 'willekeurig') {
        kluisjesList = kluisjesList.sort(() => Math.random() - 0.5)
      }
      const toewijzingen = leerlingenList.map((l, i) => ({
        kluisje_id: kluisjesList[i].id,
        leerling_stamnr: l.stamnr || l.leerling_stamnr,
        leerling_naam: l.naam || l.leerling_naam,
        leerling_klas: l.klas || l.leerling_klas,
      }))
      const res = await api.post('/api/toewijzingen/bulk', {
        toewijzingen,
        periode_van: periodeVan,
        periode_tot: periodeTot,
      })
      setResult(res)
      onDone()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const filteredLeerlingen = leerlingen.filter(l => {
    if (!leerlingFilter) return true
    const naam = (l.naam || l.leerling_naam || '').toLowerCase()
    return naam.includes(leerlingFilter.toLowerCase())
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-bold text-navy">Collectief toekennen</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-xl">✕</button>
        </div>

        {/* Step indicator */}
        <div className="px-6 py-3 border-b border-slate-100">
          <div className="flex gap-1 items-center">
            {STEPS.map((s, i) => (
              <div key={i} className="flex items-center gap-1">
                <div className={`rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold
                  ${i === step ? 'bg-navy text-white' : i < step ? 'bg-green-500 text-white' : 'bg-slate-200 text-slate-400'}`}>
                  {i < step ? '✓' : i + 1}
                </div>
                <span className={`text-xs hidden sm:block ${i === step ? 'text-navy font-medium' : 'text-slate-400'}`}>{s}</span>
                {i < STEPS.length - 1 && <div className="w-4 h-px bg-slate-200 mx-1" />}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {error && <div className="mb-3 text-sm text-red-500 bg-red-50 border border-red-200 rounded p-2">{error}</div>}

          {/* Step 0: Klas kiezen */}
          {step === 0 && (
            <div className="space-y-3">
              <p className="text-sm text-slate-600">Kies de klas waarvan u kluisjes wilt toekennen.</p>
              <div className="space-y-1 max-h-64 overflow-y-auto border rounded p-2">
                {klassen.map((k, i) => (
                  <label key={i} className="flex items-center gap-2 p-2 rounded hover:bg-slate-50 cursor-pointer">
                    <input type="radio" name="klas" value={k.naam || k} checked={selectedKlas === (k.naam || k)}
                      onChange={() => setSelectedKlas(k.naam || k)} />
                    <span className="text-sm">{k.naam || k}</span>
                  </label>
                ))}
                {klassen.length === 0 && <p className="text-sm text-slate-400 p-2">Geen klassen gevonden.</p>}
              </div>
            </div>
          )}

          {/* Step 1: Leerlingen selecteren */}
          {step === 1 && (
            <div className="space-y-3">
              <p className="text-sm text-slate-600">Selecteer de leerlingen voor klas <strong>{selectedKlas}</strong>.</p>
              <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Filter op naam..."
                value={leerlingFilter} onChange={e => setLeerlingFilter(e.target.value)} />
              <div className="flex gap-2 text-xs">
                <button className="text-navy underline" onClick={() => setSelectedLeerlingen(leerlingen.map((_, i) => i))}>
                  Alles selecteren
                </button>
                <button className="text-slate-500 underline" onClick={() => setSelectedLeerlingen([])}>
                  Niets selecteren
                </button>
                <span className="text-slate-400">{selectedLeerlingen.length} geselecteerd</span>
              </div>
              {loading && <p className="text-slate-400 text-sm">Laden...</p>}
              <div className="space-y-1 max-h-64 overflow-y-auto border rounded p-2">
                {filteredLeerlingen.map((l, fi) => {
                  const origIndex = leerlingen.indexOf(l)
                  return (
                    <label key={fi} className="flex items-center gap-2 p-1.5 rounded hover:bg-slate-50 cursor-pointer">
                      <input type="checkbox"
                        checked={selectedLeerlingen.includes(origIndex)}
                        onChange={e => {
                          if (e.target.checked) setSelectedLeerlingen(s => [...s, origIndex])
                          else setSelectedLeerlingen(s => s.filter(x => x !== origIndex))
                        }} />
                      <span className="text-sm">{l.naam || l.leerling_naam}</span>
                      <span className="text-xs text-slate-400">{l.klas || l.leerling_klas}</span>
                    </label>
                  )
                })}
              </div>
            </div>
          )}

          {/* Step 2: Periode & Kluisjes */}
          {step === 2 && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-500 mb-1">Periode van</label>
                  <input type="date" className="w-full border rounded px-2 py-1 text-sm"
                    value={periodeVan} onChange={e => setPeriodeVan(e.target.value)} />
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">Periode tot</label>
                  <input type="date" className="w-full border rounded px-2 py-1 text-sm"
                    value={periodeTot} onChange={e => setPeriodeTot(e.target.value)} />
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">Vestiging</label>
                <select className="w-full border rounded px-2 py-1 text-sm" value={selectedVestiging}
                  onChange={e => setSelectedVestiging(e.target.value)}>
                  <option value="">Kies vestiging...</option>
                  {vestigingen.map(v => <option key={v.id} value={v.id}>{v.naam}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">Cluster</label>
                <select className="w-full border rounded px-2 py-1 text-sm" value={selectedCluster}
                  onChange={e => setSelectedCluster(e.target.value)}>
                  <option value="">Kies cluster...</option>
                  {clusters.map(c => <option key={c.id} value={c.id}>{c.naam}</option>)}
                </select>
              </div>
              {availableCount !== null && (
                <div className={`text-sm p-2 rounded ${availableCount >= selectedLeerlingen.length ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'}`}>
                  Vrije kluisjes in cluster: <strong>{availableCount}</strong>
                  {' | '}Leerlingen: <strong>{selectedLeerlingen.length}</strong>
                  {availableCount < selectedLeerlingen.length && ' — Te weinig vrije kluisjes!'}
                </div>
              )}
            </div>
          )}

          {/* Step 3: Toekenningswijze */}
          {step === 3 && (
            <div className="space-y-3">
              <p className="text-sm text-slate-600">Hoe moeten kluisjes worden toegewezen?</p>
              <label className="flex items-center gap-3 p-3 border rounded hover:bg-slate-50 cursor-pointer">
                <input type="radio" name="wijze" value="volgorde" checked={toekenningWijze === 'volgorde'}
                  onChange={() => setToekenningWijze('volgorde')} />
                <div>
                  <div className="font-medium text-sm">Op volgorde</div>
                  <div className="text-xs text-slate-400">Kluisjes worden op kluisnummer oplopend toegewezen</div>
                </div>
              </label>
              <label className="flex items-center gap-3 p-3 border rounded hover:bg-slate-50 cursor-pointer">
                <input type="radio" name="wijze" value="willekeurig" checked={toekenningWijze === 'willekeurig'}
                  onChange={() => setToekenningWijze('willekeurig')} />
                <div>
                  <div className="font-medium text-sm">Willekeurig</div>
                  <div className="text-xs text-slate-400">Kluisjes worden willekeurig verdeeld</div>
                </div>
              </label>
            </div>
          )}

          {/* Step 4: Controle & Bevestigen */}
          {step === 4 && (
            <div className="space-y-3">
              <div className="bg-slate-50 rounded p-3 text-sm space-y-1">
                <div><span className="text-slate-500">Klas:</span> <strong>{selectedKlas}</strong></div>
                <div><span className="text-slate-500">Leerlingen:</span> <strong>{selectedLeerlingen.length}</strong></div>
                <div><span className="text-slate-500">Periode:</span> <strong>{periodeVan} t/m {periodeTot}</strong></div>
                <div><span className="text-slate-500">Cluster:</span> <strong>{clusters.find(c => String(c.id) === String(selectedCluster))?.naam}</strong></div>
                <div><span className="text-slate-500">Toekenning:</span> <strong>{toekenningWijze === 'volgorde' ? 'Op volgorde' : 'Willekeurig'}</strong></div>
              </div>
              <div className="border rounded overflow-hidden">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-slate-100 text-slate-500">
                      <th className="px-2 py-1 text-left">Leerling</th>
                      <th className="px-2 py-1 text-left">Stamnr</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedLeerlingen.map(i => {
                      const l = leerlingen[i]
                      return (
                        <tr key={i} className="border-t">
                          <td className="px-2 py-1">{l.naam || l.leerling_naam}</td>
                          <td className="px-2 py-1 text-slate-400">{l.stamnr || l.leerling_stamnr}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Footer buttons */}
        <div className="px-6 py-4 border-t border-slate-200 flex justify-between">
          <button onClick={step === 0 ? onClose : prevStep}
            className="border rounded px-4 py-2 text-sm text-slate-500 hover:bg-slate-50">
            {step === 0 ? 'Annuleren' : '← Terug'}
          </button>
          {step < 4 ? (
            <button onClick={nextStep} disabled={loading}
              className="bg-navy text-white rounded px-4 py-2 text-sm hover:bg-navy/90 disabled:opacity-50">
              Volgende →
            </button>
          ) : (
            <button onClick={handleSubmit} disabled={loading}
              className="bg-green-600 text-white rounded px-4 py-2 text-sm hover:bg-green-700 disabled:opacity-50">
              {loading ? 'Bezig...' : 'Toekennen'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
