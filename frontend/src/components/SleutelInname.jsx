import { useState, useRef, useEffect } from 'react'
import { api } from '../api'

/**
 * Fast intake of returned keys: type a sleutelnummer, press Enter, done.
 * Replaces the four-action flow (search, open locker, end huur, tick the box)
 * that does not scale to a counter full of keys.
 */
export default function SleutelInname({ vestigingId, onClose, onDone }) {
  const [waarde, setWaarde] = useState('')
  const [bezig, setBezig] = useState(false)
  const [fout, setFout] = useState('')
  const [keuzes, setKeuzes] = useState(null)
  const [gedaan, setGedaan] = useState([])
  const inputRef = useRef(null)

  useEffect(() => { inputRef.current?.focus() }, [])

  async function innemen(kluisjeId) {
    const nummer = waarde.trim()
    if (!nummer || bezig) return
    setBezig(true); setFout(''); setKeuzes(null)
    try {
      const body = { sleutelnummer: nummer }
      if (kluisjeId) body.kluisje_id = kluisjeId
      const res = await api.post('/api/sleutels/innemen', body)
      setGedaan(g => [res, ...g])
      setWaarde('')
    } catch (err) {
      // The 409 body carries the candidate lockers for a shared key number.
      if (err.body?.keuzes) { setKeuzes(err.body.keuzes); setFout(err.body.error) }
      else setFout(err.message)
    } finally {
      setBezig(false)
      inputRef.current?.focus()
      inputRef.current?.select()
    }
  }

  async function ongedaan(regel) {
    try {
      await api.post(`/api/sleutels/innemen/${regel.toewijzing_id}/ongedaan`)
      setGedaan(g => g.filter(r => r.toewijzing_id !== regel.toewijzing_id))
    } catch (err) { setFout(err.message) }
    inputRef.current?.focus()
  }

  function sluiten() {
    if (gedaan.length > 0) onDone()
    else onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl w-full max-w-xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-5 border-b border-slate-200 dark:border-slate-700">
          <div>
            <h2 className="text-lg font-bold text-navy dark:text-white">Sleutels innemen</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Typ of scan een sleutelnummer en druk op Enter. De huur wordt direct beëindigd met de sleutel als ingeleverd. Een deel van het nummer mag ook, dan kies je uit de treffers.
            </p>
          </div>
          <button onClick={sluiten} className="text-slate-400 hover:text-slate-600 text-2xl leading-none px-2">&times;</button>
        </div>

        <div className="p-5 space-y-3">
          <form onSubmit={e => { e.preventDefault(); innemen() }}>
            <input ref={inputRef} value={waarde} onChange={e => setWaarde(e.target.value)}
              disabled={bezig} autoComplete="off" placeholder="Sleutelnummer of deel ervan, bijvoorbeeld 2983 D of 59e"
              className="w-full border-2 border-slate-300 dark:border-slate-600 rounded-xl px-4 py-3 text-lg font-mono bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-primary/30 focus:border-primary outline-none" />
          </form>

          {fout && <p className="text-red-600 dark:text-red-400 text-sm">{fout}</p>}

          {keuzes && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-800 p-3 space-y-1">
              {keuzes.map(k => (
                <button key={k.kluisje_id} onClick={() => innemen(k.kluisje_id)}
                  className="w-full text-left px-3 py-2 rounded-lg text-sm bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 flex items-center gap-3">
                  <span className="font-semibold w-20">{k.kluisnummer}</span>
                  <span className="font-mono text-xs text-slate-400 w-20">{k.sleutelnummer}</span>
                  <span className="flex-1 truncate text-slate-600 dark:text-slate-300">{k.leerling_naam}</span>
                  <span className="text-xs text-slate-400">{k.leerling_klas}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="flex-1 overflow-auto px-5 pb-2">
          {gedaan.length === 0 ? (
            <p className="text-sm text-slate-400 dark:text-slate-500">Nog niets ingenomen.</p>
          ) : (
            <ul className="space-y-1">
              {gedaan.map(r => (
                <li key={r.toewijzing_id} className="flex items-center gap-2 text-sm py-1.5 border-b border-slate-100 dark:border-slate-700">
                  <span className="text-emerald-600">&#10003;</span>
                  <span className="font-semibold w-20">{r.kluisnummer}</span>
                  <span className="flex-1 truncate">{r.leerling_naam}</span>
                  <span className="text-xs text-slate-400 w-14">{r.leerling_klas}</span>
                  {r.borg_openstaand && (
                    <span className="text-xs text-orange-600" title="Borg staat nog open">borg</span>
                  )}
                  <button onClick={() => ongedaan(r)}
                    className="text-xs text-slate-400 hover:text-red-600 underline">ongedaan</button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="flex items-center justify-between p-5 border-t border-slate-200 dark:border-slate-700">
          <span className="text-sm font-semibold text-slate-600 dark:text-slate-300">
            {gedaan.length} sleutel(s) ingenomen
          </span>
          <button onClick={sluiten}
            className="bg-primary text-white rounded-lg px-5 py-2 text-sm font-semibold hover:bg-primary-600">
            Klaar
          </button>
        </div>
      </div>
    </div>
  )
}
