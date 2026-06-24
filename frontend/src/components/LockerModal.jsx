import { useState, useEffect } from 'react'
import { api } from '../api'
import AssignForm from './AssignForm'
import EndRentalForm from './EndRentalForm'
import { useInstellingen } from '../context/InstellingenContext'
import { formatDate } from '../utils/formatDate'

function InfoRow({ label, children }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-600 last:border-0">
      <span className="text-slate-500 dark:text-slate-400">{label}</span>
      <span className="font-medium text-right text-slate-800 dark:text-slate-200">{children}</span>
    </div>
  )
}

function StatusBadge({ status, sleutelNietIngeleverd }) {
  const cls = status === 'uitgeleend' ? 'bg-sky-100 text-sky-800 dark:bg-sky-900/50 dark:text-sky-300'
    : sleutelNietIngeleverd ? 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300'
    : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300'
  return <span className={`px-3 py-1 rounded-full font-semibold ${cls}`}>{status}</span>
}

function DefectBadge() {
  return <span className="px-3 py-1 rounded-full font-semibold bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300">defect</span>
}

export default function LockerModal({ kluisje, onClose, onUpdate }) {
  const [detail, setDetail] = useState(kluisje)
  const [geschiedenis, setGeschiedenis] = useState([])
  const [opmerkingen, setOpmerkingen] = useState(kluisje.opmerkingen || '')
  const [mode, setMode] = useState(null)
  const [savingStatus, setSavingStatus] = useState(null)
  const [editSleutel, setEditSleutel] = useState(false)
  const [sleutelInput, setSleutelInput] = useState(kluisje.sleutelnummer || '')
  const [sleutelSaving, setSleutelSaving] = useState(false)
  const [sleutelError, setSleutelError] = useState('')
  const [sleutelForce, setSleutelForce] = useState(false)
  const { borgActiefVoor } = useInstellingen()

  // Sync detail bij elke prop-update (na lijst-reload), zodat waarschuwingsblokken etc. up-to-date zijn
  useEffect(() => { setDetail(kluisje) }, [kluisje])

  const [clusters, setClusters] = useState([])
  const [verplaatsCluster, setVerplaatsCluster] = useState('')

  // Bij wisseling naar ander kluisje: opmerkingen + mode + geschiedenis resetten
  useEffect(() => {
    setOpmerkingen(kluisje.opmerkingen || '')
    setMode(null)
    setVerplaatsCluster('')
    setEditSleutel(false)
    setSleutelError('')
    setSleutelForce(false)
    setSleutelInput(kluisje.sleutelnummer || '')
    api.get(`/api/kluisjes/${kluisje.id}/geschiedenis`)
      .then(setGeschiedenis)
      .catch(() => setGeschiedenis([]))
  }, [kluisje.id])

  // Clusters van de vestiging ophalen (voor verplaats-dropdown)
  useEffect(() => {
    if (!detail.vestiging_id) { setClusters([]); return }
    api.get(`/api/vestigingen/${detail.vestiging_id}/clusters`)
      .then(setClusters)
      .catch(() => setClusters([]))
  }, [detail.vestiging_id])

  async function handleVerplaatsKluisje() {
    if (!verplaatsCluster) return
    try {
      await api.post(`/api/clusters/${verplaatsCluster}/verplaats-selectie`,
        { kluisje_ids: [detail.id] })
      setMode(null)
      setVerplaatsCluster('')
      onUpdate()
    } catch (err) {
      alert(err.message)
    }
  }

  const [ruilZoek, setRuilZoek] = useState('')
  const [ruilKandidaten, setRuilKandidaten] = useState([])
  const [ruilGekozen, setRuilGekozen] = useState(null)

  useEffect(() => {
    if (mode !== 'ruilen' || !detail.vestiging_id) return
    api.get(`/api/toewijzingen/actief?vestiging_id=${detail.vestiging_id}`)
      .then(rows => setRuilKandidaten(rows.filter(t => t.kluisje_id !== detail.id)))
      .catch(() => setRuilKandidaten([]))
  }, [mode, detail.vestiging_id, detail.id])

  const ruilFiltered = ruilKandidaten.filter(t => {
    const q = ruilZoek.trim().toLowerCase()
    if (!q) return true
    return (
      (t.kluisnummer || '').toLowerCase().includes(q) ||
      (t.leerling_naam || '').toLowerCase().includes(q) ||
      (t.leerling_stamnr || '').toLowerCase().includes(q)
    )
  })

  async function bevestigRuil() {
    if (!ruilGekozen || !detail.toewijzing_id) return
    try {
      await api.post('/api/toewijzingen/ruilen', {
        toewijzing_a_id: detail.toewijzing_id,
        toewijzing_b_id: ruilGekozen.id,
      })
      setMode(null)
      setRuilZoek(''); setRuilGekozen(null); setRuilKandidaten([])
      onUpdate()
    } catch (err) {
      alert(err.message)
    }
  }

  async function saveOpmerkingen() {
    try {
      setSavingStatus('saving')
      await api.put(`/api/kluisjes/${kluisje.id}`, { opmerkingen })
      setSavingStatus('saved')
      setTimeout(() => setSavingStatus(null), 1500)
    } catch {
      setSavingStatus('error')
    }
  }

  async function saveSleutelnummer() {
    setSleutelError('')
    const waarde = sleutelInput.trim()
    // Niets gewijzigd: gewoon sluiten.
    if (waarde === (detail.sleutelnummer || '')) { setEditSleutel(false); setSleutelForce(false); return }
    try {
      setSleutelSaving(true)
      // Sleutelnummers mogen dubbel zijn, maar waarschuw vóór opslaan.
      // Tweede klik (sleutelForce) slaat alsnog op.
      if (waarde && !sleutelForce) {
        const check = await api.get(`/api/kluisjes/${kluisje.id}/sleutel-check?waarde=${encodeURIComponent(waarde)}`)
        if (check.in_gebruik) {
          const lijst = check.kluisnummers || []
          const tekst = lijst.slice(0, 4).join(', ') + (lijst.length > 4 ? ` +${lijst.length - 4} meer` : '')
          setSleutelError(`Al in gebruik bij ${tekst}. Klik nogmaals op opslaan om toch door te gaan.`)
          setSleutelForce(true)
          return
        }
      }
      const updated = await api.put(`/api/kluisjes/${kluisje.id}`, { sleutelnummer: waarde })
      setDetail(d => ({ ...d, sleutelnummer: updated.sleutelnummer }))
      setEditSleutel(false)
      setSleutelForce(false)
      onUpdate()
    } catch (err) {
      setSleutelError(err.message)
    } finally {
      setSleutelSaving(false)
    }
  }

  function annuleerSleutel() {
    setEditSleutel(false)
    setSleutelError('')
    setSleutelForce(false)
    setSleutelInput(detail.sleutelnummer || '')
  }

  async function toggleDefect() {
    try {
      const updated = await api.put(`/api/kluisjes/${kluisje.id}`, { is_defect: !detail.is_defect })
      // Mergedetail lokaal direct (search-endpoint levert reservesleutel-velden mee, /kluisjes/:id niet)
      setDetail(d => ({ ...d, is_defect: updated.is_defect, defect_sinds: updated.defect_sinds }))
      onUpdate()
    } catch (err) {
      alert(err.message)
    }
  }

  async function toggleGeenSleutel() {
    try {
      const updated = await api.put(`/api/kluisjes/${kluisje.id}`, { geen_sleutel: !detail.geen_sleutel })
      setDetail(d => ({ ...d, geen_sleutel: updated.geen_sleutel }))
      onUpdate()
    } catch (err) {
      alert(err.message)
    }
  }

  async function toggleReservesleutel() {
    if (!detail.toewijzing_id) return
    try {
      const updated = await api.patch(`/api/toewijzingen/${detail.toewijzing_id}`, {
        reservesleutel_uitgegeven: !detail.reservesleutel_uitgegeven,
      })
      setDetail(d => ({ ...d,
        reservesleutel_uitgegeven: updated.reservesleutel_uitgegeven,
        reservesleutel_datum: updated.reservesleutel_datum,
      }))
      onUpdate()
    } catch (err) {
      alert(err.message)
    }
  }

  async function updateReservesleutelDatum(datum) {
    if (!detail.toewijzing_id) return
    try {
      const updated = await api.patch(`/api/toewijzingen/${detail.toewijzing_id}`, {
        reservesleutel_datum: datum || null,
      })
      setDetail(d => ({ ...d, reservesleutel_datum: updated.reservesleutel_datum }))
      onUpdate()
    } catch (err) {
      alert(err.message)
    }
  }

  const isUitgeleend = detail.status === 'uitgeleend'
  const isVrij = detail.status === 'vrij'
  const isDefect = !!detail.is_defect
  const geenSleutel = !!detail.geen_sleutel

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />

      <div className="relative bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] flex flex-col overflow-hidden">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-700 bg-gradient-to-r from-slate-50 to-white dark:from-slate-800 dark:to-slate-800">
          <div>
            <h2 className="text-xl font-bold text-navy dark:text-white">{detail.kluisnummer}</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">{detail.cluster_naam} — {detail.locatie || 'Geen locatie'}</p>
          </div>
          <button onClick={onClose}
            className="w-9 h-9 flex items-center justify-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">

          {/* Sleutel niet ingeleverd warning */}
          {!!detail._sleutel_niet_ingeleverd && (
            <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-xl p-4 flex items-start gap-3">
              <span className="text-xl">🔑</span>
              <div className="flex-1">
                <div className="font-semibold text-red-800 dark:text-red-300">Sleutel niet ingeleverd</div>
                <div className="text-sm text-red-600 dark:text-red-400 mt-0.5">De vorige huurder heeft de sleutel nog niet teruggebracht.</div>
                <button
                  className="mt-2 px-3 py-1.5 bg-emerald-600 text-white text-sm rounded-lg hover:bg-emerald-700 transition-colors"
                  onClick={async () => {
                    const laatste = geschiedenis.find(g => !g.actief && !g.sleutel_ingeleverd)
                    if (laatste) {
                      await api.post(`/api/toewijzingen/${laatste.id}/sleutel-ingeleverd`, {})
                      onUpdate()
                    }
                  }}>
                  Sleutel is ingeleverd
                </button>
              </div>
            </div>
          )}

          {/* Borg niet teruggestort warning */}
          {!!detail._borg_niet_teruggestort && (
            <div className="bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-800 rounded-xl p-4 flex items-start gap-3">
              <span className="text-xl">💰</span>
              <div className="flex-1">
                <div className="font-semibold text-amber-800 dark:text-amber-300">Borg niet teruggestort</div>
                <div className="text-sm text-amber-600 dark:text-amber-400 mt-0.5">De borg van de vorige huurder is nog niet terugbetaald.</div>
                <button
                  className="mt-2 px-3 py-1.5 bg-emerald-600 text-white text-sm rounded-lg hover:bg-emerald-700 transition-colors"
                  onClick={async () => {
                    const laatste = geschiedenis.find(g => !g.actief && g.borg_betaald && !g.borg_teruggestort)
                    if (laatste) {
                      await api.post(`/api/toewijzingen/${laatste.id}/borg-teruggestort`, {})
                      onUpdate()
                    }
                  }}>
                  Borg is teruggestort
                </button>
              </div>
            </div>
          )}

          {/* Basic info */}
          <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4 text-sm">
            <InfoRow label="Sleutelnummer">
              {editSleutel ? (
                <span className="flex flex-col items-end gap-1">
                  <span className="flex items-center gap-1.5">
                    <input
                      autoFocus
                      type="text"
                      value={sleutelInput}
                      onChange={e => { setSleutelInput(e.target.value); setSleutelError(''); setSleutelForce(false) }}
                      onKeyDown={e => {
                        if (e.key === 'Enter') saveSleutelnummer()
                        if (e.key === 'Escape') annuleerSleutel()
                      }}
                      placeholder="Sleutelnr"
                      className="w-32 border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg px-2 py-1 text-sm text-right outline-none focus:ring-2 focus:ring-blue-300" />
                    <button onClick={saveSleutelnummer} disabled={sleutelSaving}
                      title={sleutelForce ? 'Toch opslaan' : 'Opslaan'}
                      className={`${sleutelForce ? 'text-amber-600 hover:text-amber-700' : 'text-emerald-600 hover:text-emerald-700'} disabled:opacity-40 p-1`}>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                    </button>
                    <button onClick={annuleerSleutel} title="Annuleren"
                      className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 p-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                  </span>
                  {sleutelError && <span className={`text-xs font-normal text-right max-w-[14rem] ${sleutelForce ? 'text-amber-600 dark:text-amber-400' : 'text-red-500'}`}>{sleutelError}</span>}
                </span>
              ) : (
                <span className="flex items-center gap-2 justify-end">
                  <span>{detail.sleutelnummer || '—'}</span>
                  <button onClick={() => { setSleutelInput(detail.sleutelnummer || ''); setEditSleutel(true) }}
                    title="Sleutelnummer aanpassen"
                    className="text-slate-400 hover:text-primary p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-600 transition-colors">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                  </button>
                </span>
              )}
            </InfoRow>
            <InfoRow label="Status">
              <span className="inline-flex flex-wrap gap-1 justify-end">
                <StatusBadge status={detail.status} sleutelNietIngeleverd={detail._sleutel_niet_ingeleverd} />
                {isDefect && <DefectBadge />}
              </span>
            </InfoRow>
          </div>

          {/* Defect-info bij uitgeleend kluisje */}
          {isDefect && isUitgeleend && (
            <div className="bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-800 rounded-xl p-4 flex items-start gap-3">
              <span className="text-xl">⚠</span>
              <div className="flex-1">
                <div className="font-semibold text-amber-800 dark:text-amber-300">Defect gemeld</div>
                <div className="text-sm text-amber-600 dark:text-amber-400 mt-0.5">
                  Kluisje is gemarkeerd als defect{detail.defect_sinds && ` sinds ${formatDate(detail.defect_sinds)}`}. De huurder is intact gebleven.
                </div>
              </div>
            </div>
          )}

          {/* Huurder section */}
          {isUitgeleend && (
            <div className="bg-sky-50 dark:bg-sky-900/20 border border-sky-200 dark:border-sky-800 rounded-xl p-4">
              <div className="text-sm font-bold text-sky-800 dark:text-sky-300 mb-3 flex items-center gap-2">
                <span className="w-2.5 h-2.5 bg-sky-500 rounded-full" />
                Huidige huurder
              </div>
              <div className="text-sm space-y-0">
                <InfoRow label="Naam"><span className="font-bold text-base text-slate-900 dark:text-slate-100">{detail.leerling_naam}</span></InfoRow>
                <InfoRow label="Stamnummer"><span className="text-base">{detail.leerling_stamnr || '—'}</span></InfoRow>
                <InfoRow label="Klas"><span className="text-base">{detail.leerling_klas || '—'}</span></InfoRow>
                {detail.periode_van && (
                  <InfoRow label="Periode">{formatDate(detail.periode_van)} t/m {formatDate(detail.periode_tot)}</InfoRow>
                )}
                {borgActiefVoor(detail.vestiging_id) && detail.borgbedrag != null && detail.borgbedrag > 0 && (
                  <InfoRow label="Borg">
                    <span className={detail.borg_betaald ? 'text-emerald-700 dark:text-emerald-400 font-semibold' : 'text-amber-600 dark:text-amber-400 font-bold'}>
                      €{Number(detail.borgbedrag).toFixed(2)}
                      {detail.borg_betaald ? ' (betaald)' : ' (NIET betaald)'}
                    </span>
                  </InfoRow>
                )}
              </div>
              <div className="mt-3 pt-3 border-t border-sky-200 dark:border-sky-800 flex items-center justify-between gap-2 flex-wrap">
                <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300 cursor-pointer">
                  <input type="checkbox"
                    checked={!!detail.reservesleutel_uitgegeven}
                    onChange={toggleReservesleutel}
                    className="rounded border-slate-300 w-4 h-4" />
                  <span>🗝️ Reservesleutel uitgegeven</span>
                </label>
                {!!detail.reservesleutel_uitgegeven && (
                  <input type="date"
                    value={detail.reservesleutel_datum || ''}
                    onChange={e => updateReservesleutelDatum(e.target.value)}
                    className="text-sm border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg px-2 py-1" />
                )}
              </div>
            </div>
          )}

          {/* Forms */}
          {mode === 'toewijzen' && (
            <AssignForm kluisje={detail} onDone={() => { onUpdate(); onClose() }} onCancel={() => setMode(null)} />
          )}
          {mode === 'beeindigen' && (
            <EndRentalForm kluisje={detail} onDone={() => { onUpdate(); onClose() }} onCancel={() => setMode(null)} />
          )}

          {/* Opmerkingen */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Opmerkingen</label>
              {savingStatus === 'saving' && <span className="text-xs text-blue-500">Opslaan...</span>}
              {savingStatus === 'saved' && <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">Opgeslagen!</span>}
              {savingStatus === 'error' && <span className="text-xs text-red-500">Fout bij opslaan</span>}
            </div>
            <textarea
              className="w-full border border-slate-200 dark:border-slate-600 rounded-xl px-4 py-3 text-sm resize-none bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-300 focus:border-blue-400 outline-none transition-all"
              rows={2}
              value={opmerkingen}
              onChange={e => setOpmerkingen(e.target.value)}
              onBlur={saveOpmerkingen}
              placeholder="Notities over dit kluisje..."
            />
          </div>

          {/* Geschiedenis */}
          {geschiedenis.length > 0 && (
            <div>
              <div className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">Geschiedenis</div>
              <div className="space-y-2">
                {geschiedenis.map((g, i) => (
                  <div key={i} className="border border-slate-200 dark:border-slate-600 rounded-xl p-3 bg-slate-50/50 dark:bg-slate-700/30 text-sm">
                    <div className="flex justify-between items-start">
                      <span className="font-semibold text-slate-800 dark:text-slate-200">{g.leerling_naam}</span>
                      <span className="text-slate-400 text-xs">{g.leerling_klas}</span>
                    </div>
                    <div className="text-slate-500 dark:text-slate-400 text-xs mt-1">{formatDate(g.periode_van)} t/m {formatDate(g.periode_tot || g.einddatum) || '...'}</div>
                    <div className="flex flex-wrap gap-2 mt-2 text-xs">
                      {borgActiefVoor(detail.vestiging_id) && g.borgbedrag > 0 && (
                        g.borg_teruggestort ? (
                          <span className="text-emerald-600 dark:text-emerald-400">
                            €{Number(g.borgbedrag).toFixed(0)} terug
                          </span>
                        ) : g.borg_betaald && !g.actief ? (
                          <button
                            className="px-2 py-0.5 bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400 rounded-lg hover:bg-emerald-100 dark:hover:bg-emerald-900/40 hover:text-emerald-700 dark:hover:text-emerald-400 transition-colors font-medium"
                            onClick={async () => {
                              await api.post(`/api/toewijzingen/${g.id}/borg-teruggestort`, {})
                              onUpdate()
                            }}>
                            €{Number(g.borgbedrag).toFixed(0)} niet terug ✓
                          </button>
                        ) : (
                          <span className="text-slate-400">
                            €{Number(g.borgbedrag).toFixed(0)} niet betaald
                          </span>
                        )
                      )}
                      <span className={g.sleutel_ingeleverd ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}>
                        🔑 {g.sleutel_ingeleverd ? 'Ingeleverd' : 'Niet ingeleverd'}
                      </span>
                    </div>
                    {g.opmerking && <div className="text-slate-500 dark:text-slate-400 mt-1.5 italic text-xs">{g.opmerking}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Action buttons footer — primaire actie groot, rest subtiel */}
        {mode === null && (
          <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 space-y-3">
            {isVrij && isDefect ? (
              /* Defect + vrij: enige zinvolle actie is defect opheffen */
              <button onClick={toggleDefect}
                className="w-full text-center text-sm font-bold text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 rounded-xl py-3 border border-amber-300 dark:border-amber-700 hover:bg-amber-100 dark:hover:bg-amber-900/40 transition-colors">
                Defect opheffen
              </button>
            ) : (
              <>
                {/* Primaire actie */}
                {isVrij && !isDefect && !geenSleutel && (
                  <button onClick={() => setMode('toewijzen')}
                    className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl py-3 text-sm font-bold hover:from-blue-700 hover:to-blue-800 transition-all shadow-sm">
                    Toewijzen
                  </button>
                )}
                {isVrij && geenSleutel && (
                  <p className="text-center text-xs text-slate-500 dark:text-slate-400">
                    Geen sleutel — niet uitleenbaar tot je 'm weer als aanwezig markeert.
                  </p>
                )}
                {isUitgeleend && (
                  <button onClick={() => setMode('beeindigen')}
                    className="w-full bg-gradient-to-r from-red-500 to-red-600 text-white rounded-xl py-3 text-sm font-bold hover:from-red-600 hover:to-red-700 transition-all shadow-sm">
                    Huur beëindigen
                  </button>
                )}

                {/* Secundaire acties — kleinere knoppen, gedempt maar herkenbaar */}
                <div className="flex flex-wrap gap-2">
                  {isUitgeleend && (
                    <button onClick={() => setMode('ruilen')}
                      className="flex-1 border border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-300 rounded-lg py-2 text-xs font-medium hover:border-blue-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                      Ruilen met…
                    </button>
                  )}
                  {!isDefect ? (
                    <button onClick={toggleDefect}
                      className="flex-1 border border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-300 rounded-lg py-2 text-xs font-medium hover:border-amber-400 hover:text-amber-600 dark:hover:text-amber-400 transition-colors">
                      Markeer als defect
                    </button>
                  ) : (
                    <button onClick={toggleDefect}
                      className="flex-1 border border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-300 rounded-lg py-2 text-xs font-medium hover:border-emerald-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
                      Defect opheffen
                    </button>
                  )}
                  {/* Geen sleutel = vrij/buiten-gebruik begrip; niet tonen bij een verhuurd kluisje */}
                  {!isUitgeleend && (!geenSleutel ? (
                    <button onClick={toggleGeenSleutel}
                      className="flex-1 border border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-300 rounded-lg py-2 text-xs font-medium hover:border-rose-400 hover:text-rose-600 dark:hover:text-rose-400 transition-colors">
                      Geen sleutel
                    </button>
                  ) : (
                    <button onClick={toggleGeenSleutel}
                      className="flex-1 border border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-300 rounded-lg py-2 text-xs font-medium hover:border-emerald-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
                      Sleutel weer aanwezig
                    </button>
                  ))}
                  {clusters.length > 1 && (
                    <button onClick={() => setMode('verplaats')}
                      className="flex-1 border border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-300 rounded-lg py-2 text-xs font-medium hover:border-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors">
                      Verplaats naar cluster
                    </button>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {/* Ruilen-met paneel */}
        {mode === 'ruilen' && (
          <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 space-y-3">
            <div className="text-sm font-semibold text-slate-700 dark:text-slate-200">
              Ruilen — kies het kluisje van de andere leerling
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400">
              Beide leerlingen wisselen van kluisje. Periode, borg, sleutel en
              opmerkingen blijven per leerling ongewijzigd.
            </div>
            <input autoFocus type="text" value={ruilZoek}
              onChange={e => { setRuilZoek(e.target.value); setRuilGekozen(null) }}
              placeholder="Zoek op kluisnr, naam of stamnummer…"
              className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-300" />
            <div className="max-h-60 overflow-y-auto border border-slate-200 dark:border-slate-700 rounded-xl divide-y divide-slate-100 dark:divide-slate-700">
              {ruilFiltered.length === 0 && (
                <div className="px-4 py-3 text-sm text-slate-400">Geen verhuurde kluisjes gevonden in deze vestiging.</div>
              )}
              {ruilFiltered.map(t => (
                <button key={t.id} onClick={() => setRuilGekozen(t)}
                  className={`w-full text-left px-4 py-2.5 text-sm transition-colors ${
                    ruilGekozen && ruilGekozen.id === t.id
                      ? 'bg-blue-50 dark:bg-blue-900/30'
                      : 'hover:bg-slate-50 dark:hover:bg-slate-700/50'
                  }`}>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">{t.kluisnummer}</span>
                  <span className="text-slate-500 dark:text-slate-400"> — {t.leerling_naam || '—'}</span>
                </button>
              ))}
            </div>
            {ruilGekozen && (
              <div className="text-sm bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl px-4 py-3 text-slate-700 dark:text-slate-200">
                <span className="font-semibold">{detail.leerling_naam}</span> (kluis {detail.kluisnummer})
                {' ↔ '}
                <span className="font-semibold">{ruilGekozen.leerling_naam}</span> (kluis {ruilGekozen.kluisnummer})
              </div>
            )}
            <div className="flex gap-2">
              <button onClick={bevestigRuil} disabled={!ruilGekozen}
                className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl py-2.5 text-sm font-bold hover:from-blue-700 hover:to-blue-800 transition-all disabled:opacity-40 disabled:cursor-not-allowed">
                Ruil bevestigen
              </button>
              <button onClick={() => { setMode(null); setRuilZoek(''); setRuilGekozen(null) }}
                className="px-5 py-2.5 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors">
                Annuleren
              </button>
            </div>
          </div>
        )}

        {/* Verplaats-naar-cluster paneel */}
        {mode === 'verplaats' && (
          <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 space-y-3">
            <div className="text-sm font-semibold text-slate-700 dark:text-slate-200">
              Verplaats kluisje {detail.kluisnummer} naar een ander cluster
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400">
              Huidig cluster: {detail.cluster_naam}. De eventuele huur en
              opmerkingen blijven ongewijzigd.
            </div>
            <select value={verplaatsCluster} onChange={e => setVerplaatsCluster(e.target.value)}
              className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-300">
              <option value="">— kies doelcluster —</option>
              {clusters.filter(c => String(c.id) !== String(detail.cluster_id)).map(c => (
                <option key={c.id} value={c.id}>{c.naam}</option>
              ))}
            </select>
            <div className="flex gap-2">
              <button onClick={handleVerplaatsKluisje} disabled={!verplaatsCluster}
                className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl py-2.5 text-sm font-bold hover:from-blue-700 hover:to-blue-800 transition-all disabled:opacity-40 disabled:cursor-not-allowed">
                Verplaatsen
              </button>
              <button onClick={() => { setMode(null); setVerplaatsCluster('') }}
                className="px-5 py-2.5 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors">
                Annuleren
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
