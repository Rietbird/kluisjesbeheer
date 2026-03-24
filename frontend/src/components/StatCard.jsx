export default function StatCard({ label, value, color = 'text-navy' }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 text-center flex-1 min-w-[100px]">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-slate-400 mt-1">{label}</div>
    </div>
  )
}
