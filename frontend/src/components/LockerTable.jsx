import { useInstellingen } from '../context/InstellingenContext'
import { formatDate } from '../utils/formatDate'

function StatusBadge({ kluisje }) {
  const cls = kluisje.status === 'uitgeleend' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300'
    : kluisje.status === 'defect' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300'
    : kluisje._sleutel_niet_ingeleverd ? 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300'
    : 'bg-sky-100 text-sky-700 dark:bg-sky-900/50 dark:text-sky-300'
  const label = kluisje._sleutel_niet_ingeleverd && kluisje.status === 'vrij'
    ? '🔑 Vrij' : kluisje.status
  return <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${cls}`}>{label}</span>
}

export default function LockerTable({ kluisjes, onSelect, selectedId }) {
  const { borgActiefVoor } = useInstellingen()
  const vestigingId = kluisjes[0]?.vestiging_id
  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-50 dark:bg-slate-700 border-b border-slate-200 dark:border-slate-600">
            <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-600">Kluisnr</th>
            <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-600 hidden md:table-cell">Sleutelnr</th>
            <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-600">Naam</th>
            <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-600 hidden md:table-cell">Stamnr</th>
            <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-600 hidden lg:table-cell">Klas</th>
            <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-600">Status</th>
            {borgActiefVoor(vestigingId) && <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-600 hidden lg:table-cell">Borg</th>}
            <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-600 hidden md:table-cell">Periode</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {kluisjes.map(k => (
            <tr key={k.id} onClick={() => onSelect(k)}
              className={`cursor-pointer transition-colors ${selectedId === k.id ? 'bg-navy/5 dark:bg-slate-700' : 'hover:bg-slate-50 dark:hover:bg-slate-700'}`}>
              <td className="px-3 py-2 font-semibold text-navy">{k.kluisnummer}</td>
              <td className="px-3 py-2 hidden md:table-cell text-slate-400 text-xs">{k.sleutelnummer || '—'}</td>
              <td className="px-3 py-2">{k.leerling_naam || <span className="text-slate-300">—</span>}</td>
              <td className="px-3 py-2 hidden md:table-cell text-slate-400 text-xs">{k.leerling_stamnr || '—'}</td>
              <td className="px-3 py-2 hidden lg:table-cell text-xs">{k.leerling_klas || '—'}</td>
              <td className="px-3 py-2"><StatusBadge kluisje={k} /></td>
              {borgActiefVoor(vestigingId) && (
                <td className="px-3 py-2 hidden lg:table-cell text-xs text-slate-500">
                  {k.borgbedrag > 0 ? (
                    <span className={k.borg_betaald ? 'text-green-600' : 'text-amber-600'}>
                      €{Number(k.borgbedrag).toFixed(0)} {k.borg_betaald ? '✓' : '✗'}
                    </span>
                  ) : '—'}
                </td>
              )}
              <td className="px-3 py-2 hidden md:table-cell text-xs text-slate-400">
                {k.periode_van && k.periode_tot ? `${formatDate(k.periode_van)} t/m ${formatDate(k.periode_tot)}` : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
