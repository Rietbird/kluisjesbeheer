function getColor(kluisje) {
  if (kluisje.status === 'defect') return 'bg-amber-100 border-amber-300'
  if (kluisje.status === 'uitgeleend') return 'bg-green-100 border-green-300'
  if (kluisje.status === 'vrij' && kluisje._sleutel_niet_ingeleverd) return 'bg-red-100 border-red-300'
  return 'bg-blue-100 border-blue-300'
}

function getLabel(kluisje) {
  if (kluisje.status === 'defect') return <span className="text-amber-600 text-[7px]">Defect</span>
  if (kluisje.status === 'uitgeleend' && kluisje.leerling_naam) {
    const parts = kluisje.leerling_naam.split(' ')
    const short = parts[0] + (parts.length > 1 ? ` ${parts[parts.length - 1][0]}.` : '')
    return <span className="text-green-600 text-[7px]">{short}</span>
  }
  if (kluisje._sleutel_niet_ingeleverd) return <span className="text-red-600 text-[7px]">🔑!</span>
  return <span className="text-blue-600 text-[7px]">Vrij</span>
}

export default function LockerGrid({ kluisjes, onSelect, selectedId }) {
  return (
    <div>
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-1.5">
        {kluisjes.map(k => (
          <button key={k.id} onClick={() => onSelect(k)}
            className={`${getColor(k)} border rounded p-1.5 text-center cursor-pointer hover:shadow transition-shadow
              ${selectedId === k.id ? 'ring-2 ring-blue-500 shadow-md' : ''}`}>
            <div className="font-bold text-[10px]">{k.kluisnummer}</div>
            {getLabel(k)}
          </button>
        ))}
      </div>
      <div className="mt-3 flex gap-4 text-[9px] text-slate-400">
        <span><span className="inline-block w-2 h-2 bg-green-100 border border-green-300 rounded-sm mr-1" />Uitgeleend</span>
        <span><span className="inline-block w-2 h-2 bg-blue-100 border border-blue-300 rounded-sm mr-1" />Vrij</span>
        <span><span className="inline-block w-2 h-2 bg-amber-100 border border-amber-300 rounded-sm mr-1" />Defect</span>
        <span><span className="inline-block w-2 h-2 bg-red-100 border border-red-300 rounded-sm mr-1" />Sleutel niet ingeleverd</span>
      </div>
    </div>
  )
}
