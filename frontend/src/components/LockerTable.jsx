import { useState, useMemo } from 'react'
import { useInstellingen } from '../context/InstellingenContext'
import { formatDate } from '../utils/formatDate'

function SortIcon({ col, sortCol, sortDir }) {
  if (sortCol !== col) {
    return (
      <svg className="w-3 h-3 inline-block ml-1 text-slate-400 opacity-50" viewBox="0 0 10 14" fill="currentColor">
        <path d="M5 0L9 5H1L5 0Z" />
        <path d="M5 14L1 9H9L5 14Z" />
      </svg>
    )
  }
  if (sortDir === 'asc') {
    return (
      <svg className="w-3 h-3 inline-block ml-1 text-navy dark:text-slate-200" viewBox="0 0 10 14" fill="currentColor">
        <path d="M5 0L9 7H1L5 0Z" />
      </svg>
    )
  }
  return (
    <svg className="w-3 h-3 inline-block ml-1 text-navy dark:text-slate-200" viewBox="0 0 10 14" fill="currentColor">
      <path d="M5 14L1 7H9L5 14Z" />
    </svg>
  )
}

function StatusBadge({ kluisje }) {
  const hasWarning = kluisje._sleutel_niet_ingeleverd || kluisje._borg_niet_teruggestort
  const cls = kluisje.status === 'uitgeleend' ? 'bg-sky-100 text-sky-700 dark:bg-sky-900/50 dark:text-sky-300'
    : kluisje.status === 'defect' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300'
    : hasWarning ? 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300'
    : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300'
  let label = kluisje.status
  if (kluisje.status === 'vrij' && hasWarning) {
    const icons = []
    if (kluisje._sleutel_niet_ingeleverd) icons.push('🔑')
    if (kluisje._borg_niet_teruggestort) icons.push('💰')
    label = `${icons.join('')} Vrij`
  }
  return <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${cls}`}>{label}</span>
}

export default function LockerTable({ kluisjes, onSelect, selectedId }) {
  const { borgActiefVoor } = useInstellingen()
  const vestigingId = kluisjes[0]?.vestiging_id
  const [sortCol, setSortCol] = useState(null)
  const [sortDir, setSortDir] = useState('asc')

  function handleSort(col) {
    if (sortCol === col) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortCol(col)
      setSortDir('asc')
    }
  }

  const sorted = useMemo(() => {
    if (!sortCol) return kluisjes
    return [...kluisjes].sort((a, b) => {
      let aVal, bVal
      if (sortCol === 'kluisnummer') { aVal = a.kluisnummer || ''; bVal = b.kluisnummer || '' }
      else if (sortCol === 'naam') { aVal = a.leerling_naam || ''; bVal = b.leerling_naam || '' }
      else if (sortCol === 'klas') { aVal = a.leerling_klas || ''; bVal = b.leerling_klas || '' }
      else if (sortCol === 'status') { aVal = a.status || ''; bVal = b.status || '' }
      else if (sortCol === 'periode') { aVal = a.periode_tot || ''; bVal = b.periode_tot || '' }
      else { aVal = ''; bVal = '' }
      const cmp = aVal.localeCompare(bVal, undefined, { numeric: true, sensitivity: 'base' })
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [kluisjes, sortCol, sortDir])

  const thSortCls = 'px-3 py-2.5 text-left text-xs font-semibold text-slate-600 dark:text-slate-300 cursor-pointer select-none hover:text-navy dark:hover:text-white transition-colors'
  const thCls = 'px-3 py-2.5 text-left text-xs font-semibold text-slate-600 dark:text-slate-300'

  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-50 dark:bg-slate-700 border-b border-slate-200 dark:border-slate-600">
            <th className={thSortCls} onClick={() => handleSort('kluisnummer')}>
              Kluisnr<SortIcon col="kluisnummer" sortCol={sortCol} sortDir={sortDir} />
            </th>
            <th className={`${thCls} hidden md:table-cell`}>Sleutelnr</th>
            <th className={thSortCls} onClick={() => handleSort('naam')}>
              Naam<SortIcon col="naam" sortCol={sortCol} sortDir={sortDir} />
            </th>
            <th className={`${thCls} hidden md:table-cell`}>Stamnr</th>
            <th className={`${thSortCls} hidden lg:table-cell`} onClick={() => handleSort('klas')}>
              Klas<SortIcon col="klas" sortCol={sortCol} sortDir={sortDir} />
            </th>
            <th className={thSortCls} onClick={() => handleSort('status')}>
              Status<SortIcon col="status" sortCol={sortCol} sortDir={sortDir} />
            </th>
            {borgActiefVoor(vestigingId) && <th className={`${thCls} hidden lg:table-cell`}>Borg</th>}
            <th className={`${thSortCls} hidden md:table-cell`} onClick={() => handleSort('periode')}>
              Periode<SortIcon col="periode" sortCol={sortCol} sortDir={sortDir} />
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
          {sorted.map(k => (
            <tr key={k.id} onClick={() => onSelect(k)}
              className={`cursor-pointer transition-colors ${selectedId === k.id ? 'bg-navy/5 dark:bg-slate-700' : 'hover:bg-slate-50 dark:hover:bg-slate-700'}`}>
              <td className="px-3 py-2 font-semibold text-navy dark:text-slate-100">{k.kluisnummer}</td>
              <td className="px-3 py-2 hidden md:table-cell text-slate-400 dark:text-slate-500 text-xs">{k.sleutelnummer || '—'}</td>
              <td className="px-3 py-2 text-slate-800 dark:text-slate-200">{k.leerling_naam || <span className="text-slate-300 dark:text-slate-600">—</span>}{k.leerling_vertrokken_op && <span className="ml-1 text-xs text-red-600 font-bold">[V]</span>}</td>
              <td className="px-3 py-2 hidden md:table-cell text-slate-400 dark:text-slate-500 text-xs">{k.leerling_stamnr || '—'}</td>
              <td className="px-3 py-2 hidden lg:table-cell text-xs text-slate-600 dark:text-slate-400">{k.leerling_klas || '—'}</td>
              <td className="px-3 py-2"><StatusBadge kluisje={k} /></td>
              {borgActiefVoor(vestigingId) && (
                <td className="px-3 py-2 hidden lg:table-cell text-xs text-slate-500 dark:text-slate-400">
                  {k.borgbedrag > 0 ? (
                    <span className={k.borg_betaald ? 'text-green-600 dark:text-green-400' : 'text-amber-600 dark:text-amber-400'}>
                      €{Number(k.borgbedrag).toFixed(0)} {k.borg_betaald ? '✓' : '✗'}
                    </span>
                  ) : '—'}
                </td>
              )}
              <td className="px-3 py-2 hidden md:table-cell text-xs text-slate-400 dark:text-slate-500">
                {k.periode_van && k.periode_tot ? `${formatDate(k.periode_van)} t/m ${formatDate(k.periode_tot)}` : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
