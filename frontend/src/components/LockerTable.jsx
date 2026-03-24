export default function LockerTable({ kluisjes, onSelect, selectedId }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-100 text-left text-xs text-slate-500">
            <th className="px-3 py-2">Kluisnr</th>
            <th className="px-3 py-2 hidden md:table-cell">Sleutelnr</th>
            <th className="px-3 py-2">Naam</th>
            <th className="px-3 py-2 hidden md:table-cell">Stamnr</th>
            <th className="px-3 py-2 hidden md:table-cell">Klas</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2 hidden md:table-cell">Periode</th>
          </tr>
        </thead>
        <tbody>
          {kluisjes.map(k => (
            <tr key={k.id} onClick={() => onSelect(k)}
              className={`border-t cursor-pointer hover:bg-blue-50 ${selectedId === k.id ? 'bg-blue-50' : ''}`}>
              <td className="px-3 py-2 font-semibold text-navy">{k.kluisnummer}</td>
              <td className="px-3 py-2 hidden md:table-cell text-slate-400">{k.sleutelnummer}</td>
              <td className="px-3 py-2">{k.leerling_naam || <span className="text-slate-300">—</span>}</td>
              <td className="px-3 py-2 hidden md:table-cell text-slate-400">{k.leerling_stamnr || '—'}</td>
              <td className="px-3 py-2 hidden md:table-cell">{k.leerling_klas || '—'}</td>
              <td className="px-3 py-2">
                <span className={`text-xs px-2 py-0.5 rounded ${
                  k.status === 'uitgeleend' ? 'bg-green-100 text-green-600' :
                  k.status === 'defect' ? 'bg-amber-100 text-amber-600' :
                  'bg-blue-100 text-blue-600'
                }`}>{k.status}</span>
              </td>
              <td className="px-3 py-2 hidden md:table-cell text-xs text-slate-400">
                {k.periode_van && k.periode_tot ? `${k.periode_van} t/m ${k.periode_tot}` : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
