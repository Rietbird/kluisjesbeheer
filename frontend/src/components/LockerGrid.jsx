function getColor(kluisje) {
  if (kluisje.status === 'defect')
    return 'bg-amber-50 border-amber-400 hover:bg-amber-100 dark:bg-amber-900/40 dark:border-amber-600 dark:hover:bg-amber-900/60'
  if (kluisje.status === 'uitgeleend' && kluisje.borgbedrag > 0 && !kluisje.borg_betaald)
    return 'bg-orange-50 border-orange-400 hover:bg-orange-100 dark:bg-orange-900/40 dark:border-orange-500 dark:hover:bg-orange-900/60'
  if (kluisje.status === 'uitgeleend')
    return 'bg-sky-50 border-sky-400 hover:bg-sky-100 dark:bg-sky-900/40 dark:border-sky-600 dark:hover:bg-sky-900/60'
  if (kluisje.status === 'vrij' && (kluisje._sleutel_niet_ingeleverd || kluisje._borg_niet_teruggestort))
    return 'bg-red-50 border-red-400 hover:bg-red-100 dark:bg-red-900/40 dark:border-red-600 dark:hover:bg-red-900/60'
  return 'bg-emerald-50 border-emerald-300 hover:bg-emerald-100 dark:bg-emerald-900/40 dark:border-emerald-600 dark:hover:bg-emerald-900/60'
}

function getLabel(kluisje) {
  if (kluisje.status === 'defect') return <span className="text-amber-700 dark:text-amber-400 font-semibold">Defect</span>
  if (kluisje.status === 'uitgeleend') {
    const borgNietBetaald = kluisje.borgbedrag > 0 && !kluisje.borg_betaald
    const parts = kluisje.leerling_naam ? kluisje.leerling_naam.split(' ') : []
    const short = parts.length > 0
      ? parts[0] + (parts.length > 1 ? ` ${parts[parts.length - 1][0]}.` : '')
      : ''
    return (
      <span className={`truncate block ${borgNietBetaald ? 'text-orange-700 dark:text-orange-300' : 'text-sky-800 dark:text-sky-300'}`}>
        {borgNietBetaald && <span className="mr-0.5">💰</span>}{kluisje.leerling_vertrokken_op && <span className="text-red-600 mr-0.5" title="Vertrokken van school">⚠</span>}{short}
      </span>
    )
  }
  if (kluisje._sleutel_niet_ingeleverd && kluisje._borg_niet_teruggestort) return <span className="text-red-700 dark:text-red-400 font-semibold">🔑💰</span>
  if (kluisje._sleutel_niet_ingeleverd) return <span className="text-red-700 dark:text-red-400 font-semibold">🔑 Sleutel!</span>
  if (kluisje._borg_niet_teruggestort) return <span className="text-red-700 dark:text-red-400 font-semibold">💰 Borg!</span>
  return <span className="text-emerald-500 dark:text-emerald-400 font-medium">Vrij</span>
}

export default function LockerGrid({ kluisjes, onSelect, selectedId }) {
  return (
    <div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-2.5">
        {kluisjes.map(k => (
          <button key={k.id} onClick={() => onSelect(k)}
            className={`${getColor(k)} border-2 rounded-xl p-3 text-center cursor-pointer transition-all
              ${selectedId === k.id ? 'ring-3 ring-blue-500 shadow-lg scale-[1.04]' : 'hover:shadow-md'}`}>
            <div className="font-bold text-base text-slate-900 dark:text-white">{k.kluisnummer}</div>
            <div className="text-sm mt-1 truncate">{getLabel(k)}</div>
          </button>
        ))}
      </div>
      <div className="mt-5 flex flex-wrap gap-6 text-sm text-slate-600 dark:text-slate-400">
        <span className="flex items-center gap-2"><span className="w-4 h-4 bg-sky-50 dark:bg-sky-900/40 border-2 border-sky-400 dark:border-sky-600 rounded-lg" />Uitgeleend</span>
        <span className="flex items-center gap-2"><span className="w-4 h-4 bg-orange-50 dark:bg-orange-900/40 border-2 border-orange-400 dark:border-orange-500 rounded-lg" />💰 Borg niet betaald</span>
        <span className="flex items-center gap-2"><span className="w-4 h-4 bg-emerald-50 dark:bg-emerald-900/40 border-2 border-emerald-300 dark:border-emerald-600 rounded-lg" />Vrij</span>
        <span className="flex items-center gap-2"><span className="w-4 h-4 bg-amber-50 dark:bg-amber-900/40 border-2 border-amber-400 dark:border-amber-600 rounded-lg" />Defect</span>
        <span className="flex items-center gap-2"><span className="w-4 h-4 bg-red-50 dark:bg-red-900/40 border-2 border-red-400 dark:border-red-600 rounded-lg" />🔑 Sleutel / 💰 Borg openstaand (vrij)</span>
      </div>
    </div>
  )
}
