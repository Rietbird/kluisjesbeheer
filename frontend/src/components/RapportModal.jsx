import { useState, useEffect } from 'react'
import { useInstellingen } from '../context/InstellingenContext'

const OVERZICHTEN = [
  { type: 'toewijzingen', label: 'Actieve toewijzingen', hint: 'Alle lopende huren' },
  { type: 'inname', label: 'Innameoverzicht', hint: 'Afvinklijst voor de balie' },
  { type: 'defect', label: 'Defecte kluisjes', hint: 'Wat er stuk is' },
  { type: 'zonder_kluisje', label: 'Leerlingen zonder kluisje', hint: 'Wie er nog een nodig heeft' },
]

const OPENSTAAND = [
  { type: 'sleutels', label: 'Openstaande sleutels', hint: 'Huur afgesloten, sleutel niet terug' },
  { type: 'vertrokken', label: 'Vertrokken leerlingen', hint: 'Per schooljaar, met sleutelstatus' },
]

const EyeIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
  </svg>
)

const DownloadIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
)

function RapportRij({ label, hint, onDownload, onPreview }) {
  return (
    <div className="flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-700/60 transition-colors">
      <button onClick={onDownload}
        className="flex-1 text-left cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 rounded">
        <span className="block text-sm font-semibold text-navy dark:text-white">{label}</span>
        <span className="block text-xs text-slate-500 dark:text-slate-400">{hint}</span>
      </button>
      <button onClick={onPreview} title="Preview" aria-label={`Preview ${label}`}
        className="shrink-0 p-2 rounded-lg text-slate-400 hover:text-primary hover:bg-white dark:hover:bg-slate-600 cursor-pointer transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40">
        <EyeIcon />
      </button>
    </div>
  )
}

export default function RapportModal({ vestigingId, klas, klassen, onClose }) {
  const [selectie, setSelectie] = useState(klas ? [klas] : [])
  const [zoek, setZoek] = useState('')
  const { borgActiefVoor } = useInstellingen()

  useEffect(() => {
    const opToets = e => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', opToets)
    return () => window.removeEventListener('keydown', opToets)
  }, [onClose])

  // Een array-waarde wordt herhaald in de querystring (klas=M4A&klas=M4B), want
  // het per-klas rapport zet meerdere klassen in één PDF.
  function bouwParams(type, extra) {
    const params = new URLSearchParams({ type })
    if (vestigingId) params.set('vestiging_id', vestigingId)
    Object.entries(extra).forEach(([k, v]) => {
      if (Array.isArray(v)) v.forEach(item => item && params.append(k, item))
      else if (v) params.set(k, v)
    })
    return params
  }

  function open(pad, type, extra = {}) {
    window.open(`/api/dashboard/${pad}?${bouwParams(type, extra)}`, '_blank')
  }

  const download = (type, extra) => open('rapport', type, extra)
  const preview = (type, extra) => open('rapport/preview', type, extra)

  const zichtbaar = klassen.filter(k => k.toLowerCase().includes(zoek.toLowerCase()))
  const allesAan = zichtbaar.length > 0 && zichtbaar.every(k => selectie.includes(k))

  function toggle(k) {
    setSelectie(s => s.includes(k) ? s.filter(x => x !== k) : [...s, k])
  }

  function toggleAlles() {
    setSelectie(s => allesAan
      ? s.filter(k => !zichtbaar.includes(k))
      : [...new Set([...s, ...zichtbaar])])
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}>
      <div role="dialog" aria-modal="true" aria-labelledby="rapport-titel"
        onClick={e => e.stopPropagation()}
        className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col">

        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <div>
            <h2 id="rapport-titel" className="text-lg font-bold text-navy dark:text-white">Rapport</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Klik op een rapport om de PDF te downloaden, of op het oogje voor een preview.
            </p>
          </div>
          <button onClick={onClose} aria-label="Sluiten"
            className="p-2 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 cursor-pointer transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto grid md:grid-cols-2 gap-y-6 p-6">
          <div className="md:pr-6">
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide px-3 mb-1">Overzichten</h3>
            {OVERZICHTEN.map(r => (
              <RapportRij key={r.type} {...r}
                onDownload={() => download(r.type)} onPreview={() => preview(r.type)} />
            ))}

            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide px-3 mt-4 mb-1">Openstaand</h3>
            {OPENSTAAND.map(r => (
              <RapportRij key={r.type} {...r}
                onDownload={() => download(r.type)} onPreview={() => preview(r.type)} />
            ))}
            {borgActiefVoor(vestigingId) && (
              <RapportRij label="Openstaande borg" hint="Nog te betalen of terug te storten"
                onDownload={() => download('borg')} onPreview={() => preview('borg')} />
            )}
          </div>

          <div className="flex flex-col min-h-0 md:pl-6 md:border-l md:border-slate-200 md:dark:border-slate-700">
            <div className="flex items-baseline justify-between px-3 mb-1">
              <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Per klas</h3>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {selectie.length} geselecteerd
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 px-3 mb-2">
              Eén PDF, elke klas op een eigen bladzijde.
            </p>

            {klassen.length === 0 ? (
              <p className="text-sm text-slate-400 px-3 py-4">
                Kies eerst een vestiging om de klassen te zien.
              </p>
            ) : (
              <>
                <div className="flex gap-2 px-3 mb-2">
                  <input value={zoek} onChange={e => setZoek(e.target.value)}
                    placeholder="Zoek klas..." aria-label="Zoek klas"
                    className="flex-1 min-w-0 border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-1.5 text-sm dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-primary/30 focus:border-primary outline-none" />
                  <button onClick={toggleAlles}
                    className="shrink-0 text-sm text-primary hover:underline cursor-pointer px-2 rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40">
                    {allesAan ? 'Niets' : 'Alles'}
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto border border-slate-200 dark:border-slate-700 rounded-lg p-2 grid grid-cols-2 gap-x-2 content-start min-h-[8rem] max-h-64">
                  {zichtbaar.map(k => (
                    <label key={k}
                      className="flex items-center gap-2 px-2 py-1.5 rounded text-sm cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">
                      <input type="checkbox" checked={selectie.includes(k)} onChange={() => toggle(k)}
                        className="rounded border-slate-300 text-primary focus:ring-primary/30 cursor-pointer" />
                      <span className="truncate text-slate-700 dark:text-slate-200">{k}</span>
                    </label>
                  ))}
                  {zichtbaar.length === 0 && (
                    <p className="col-span-2 text-sm text-slate-400 p-2">Geen klas gevonden.</p>
                  )}
                </div>

                <div className="flex gap-2 mt-3 px-3">
                  <button disabled={selectie.length === 0}
                    onClick={() => download('klas', { klas: selectie })}
                    className="flex-1 flex items-center justify-center gap-2 bg-primary text-white rounded-lg px-4 py-2.5 text-sm font-medium hover:bg-primary-600 disabled:bg-slate-200 dark:disabled:bg-slate-700 disabled:text-slate-400 disabled:cursor-not-allowed cursor-pointer transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40">
                    <DownloadIcon />
                    Download ({selectie.length})
                  </button>
                  <button disabled={selectie.length === 0}
                    onClick={() => preview('klas', { klas: selectie })}
                    aria-label="Preview van de geselecteerde klassen" title="Preview"
                    className="shrink-0 p-2.5 rounded-lg border border-slate-300 dark:border-slate-600 text-slate-500 dark:text-slate-300 hover:text-primary hover:border-primary disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40">
                    <EyeIcon />
                  </button>
                </div>

                <button onClick={() => download('klas')}
                  className="mt-2 mx-3 text-sm text-slate-500 dark:text-slate-400 hover:text-primary cursor-pointer text-left rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40">
                  Of download alle klassen in één keer
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
