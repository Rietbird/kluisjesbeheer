import { useState, useEffect } from 'react'
import { api } from '../api'

export default function Instellingen() {
  const [settings, setSettings] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState('')

  // Periode settings
  const [periodeVan, setPeriodeVan] = useState('')
  const [periodeTot, setPeriodeTot] = useState('')

  // CSV Import
  const [vestigingen, setVestigingen] = useState([])
  const [clusters, setClusters] = useState([])
  const [importVestiging, setImportVestiging] = useState('')
  const [importCluster, setImportCluster] = useState('')
  const [importFile, setImportFile] = useState(null)
  const [importing, setImporting] = useState(false)
  const [importMsg, setImportMsg] = useState('')
  const [importError, setImportError] = useState('')

  useEffect(() => {
    api.get('/api/instellingen')
      .then(data => {
        setSettings(data)
        setPeriodeVan(data.standaard_periode_van || '')
        setPeriodeTot(data.standaard_periode_tot || '')
      })
      .catch(() => {})
      .finally(() => setLoading(false))
    api.get('/api/vestigingen').then(setVestigingen).catch(() => {})
  }, [])

  useEffect(() => {
    if (importVestiging) {
      api.get(`/api/vestigingen/${importVestiging}/clusters`).then(setClusters).catch(() => {})
    } else {
      setClusters([])
    }
    setImportCluster('')
  }, [importVestiging])

  async function handleSavePeriode(e) {
    e.preventDefault()
    setSaving(true)
    setSaveMsg('')
    try {
      await api.put('/api/instellingen', {
        standaard_periode_van: periodeVan,
        standaard_periode_tot: periodeTot,
      })
      setSaveMsg('Opgeslagen!')
      setTimeout(() => setSaveMsg(''), 2000)
    } catch (err) {
      setSaveMsg(`Fout: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  async function handleImport(e) {
    e.preventDefault()
    if (!importCluster || !importFile) {
      setImportError('Kies een cluster en een bestand.')
      return
    }
    setImporting(true)
    setImportMsg('')
    setImportError('')
    try {
      const formData = new FormData()
      formData.append('cluster_id', importCluster)
      formData.append('file', importFile)
      const res = await api.upload('/api/kluisjes/import', formData)
      setImportMsg(`Import geslaagd: ${res.imported ?? res.count ?? '?'} kluisjes geïmporteerd.`)
      setImportFile(null)
      // Reset file input
      const fileInput = document.getElementById('csv-file-input')
      if (fileInput) fileInput.value = ''
    } catch (err) {
      setImportError(`Import mislukt: ${err.message}`)
    } finally {
      setImporting(false)
    }
  }

  if (loading) return <div className="p-4 text-slate-500">Laden...</div>

  return (
    <div className="p-4 max-w-2xl mx-auto space-y-6">
      <h1 className="text-xl font-bold text-navy">Instellingen</h1>

      {/* Standaard uitleenperiode */}
      <div className="bg-white border border-slate-200 rounded-lg p-4">
        <h2 className="text-sm font-bold text-slate-700 mb-3">Standaard uitleenperiode</h2>
        <form onSubmit={handleSavePeriode} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1">Van (MM-DD)</label>
              <input
                className="w-full border rounded px-2 py-1 text-sm"
                placeholder="09-01"
                value={periodeVan}
                onChange={e => setPeriodeVan(e.target.value)}
                pattern="\d{2}-\d{2}"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Tot (MM-DD)</label>
              <input
                className="w-full border rounded px-2 py-1 text-sm"
                placeholder="07-31"
                value={periodeTot}
                onChange={e => setPeriodeTot(e.target.value)}
                pattern="\d{2}-\d{2}"
              />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button type="submit" disabled={saving}
              className="bg-navy text-white rounded px-4 py-1.5 text-sm hover:bg-navy/90 disabled:opacity-50">
              {saving ? 'Opslaan...' : 'Opslaan'}
            </button>
            {saveMsg && (
              <span className={`text-sm ${saveMsg.startsWith('Fout') ? 'text-red-500' : 'text-green-600'}`}>
                {saveMsg}
              </span>
            )}
          </div>
        </form>
      </div>

      {/* CSV Import */}
      <div className="bg-white border border-slate-200 rounded-lg p-4">
        <h2 className="text-sm font-bold text-slate-700 mb-3">CSV Import kluisjes</h2>
        <form onSubmit={handleImport} className="space-y-3">
          <div>
            <label className="block text-xs text-slate-500 mb-1">Vestiging</label>
            <select className="w-full border rounded px-2 py-1 text-sm" value={importVestiging}
              onChange={e => setImportVestiging(e.target.value)}>
              <option value="">Kies vestiging...</option>
              {vestigingen.map(v => <option key={v.id} value={v.id}>{v.naam}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Cluster</label>
            <select className="w-full border rounded px-2 py-1 text-sm" value={importCluster}
              onChange={e => setImportCluster(e.target.value)} disabled={!importVestiging}>
              <option value="">Kies cluster...</option>
              {clusters.map(c => <option key={c.id} value={c.id}>{c.naam}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">CSV-bestand</label>
            <input
              id="csv-file-input"
              type="file"
              accept=".csv"
              className="w-full text-sm text-slate-600 file:mr-3 file:py-1 file:px-3 file:rounded file:border file:text-xs file:border-slate-300 file:bg-slate-50 hover:file:bg-slate-100"
              onChange={e => setImportFile(e.target.files[0] || null)}
            />
            <p className="text-xs text-slate-400 mt-1">Verwacht formaat: kluisnummer, sleutelnummer, locatie (header optioneel)</p>
          </div>
          {importError && <p className="text-red-500 text-xs">{importError}</p>}
          {importMsg && <p className="text-green-600 text-sm">{importMsg}</p>}
          <button type="submit" disabled={importing}
            className="bg-navy text-white rounded px-4 py-1.5 text-sm hover:bg-navy/90 disabled:opacity-50">
            {importing ? 'Importeren...' : 'Importeren'}
          </button>
        </form>
      </div>
    </div>
  )
}
