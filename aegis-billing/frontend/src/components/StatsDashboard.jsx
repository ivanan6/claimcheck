import { TrendingUp, ShieldOff, Activity, Timer } from 'lucide-react'
import { motion } from 'framer-motion'

export default function StatsDashboard({ stats }) {
  if (!stats) stats = { total_intercepted: 0, errors_blocked: 0, saved_eur: 0, avg_processing_ms: 0 }

  const items = [
    { icon: Activity, label: 'Presretnuto racuna', value: stats.total_intercepted, suffix: '', color: 'text-aegis-accent', bg: 'bg-aegis-accent/10' },
    { icon: ShieldOff, label: 'Blokirano gresaka', value: stats.errors_blocked, suffix: '', color: 'text-aegis-danger', bg: 'bg-aegis-danger/10' },
    { icon: TrendingUp, label: 'Sacuvano klinikama', value: stats.saved_eur, suffix: ' €', color: 'text-aegis-success', bg: 'bg-aegis-success/10', decimals: 2 },
    { icon: Timer, label: 'Prosek obrade', value: stats.avg_processing_ms / 1000, suffix: 's', color: 'text-aegis-accent2', bg: 'bg-aegis-accent2/10', decimals: 1 },
  ]

  return (
    <div className="grid grid-cols-4 gap-3">
      {items.map((it, i) => <StatCard key={i} {...it} />)}
    </div>
  )
}

function StatCard({ icon: Icon, label, value, suffix, color, bg, decimals = 0 }) {
  return (
    <motion.div layout className="bg-aegis-panel/80 backdrop-blur-sm border border-aegis-border rounded-xl p-3 flex items-center gap-3">
      <div className={`w-10 h-10 rounded-lg ${bg} flex items-center justify-center ${color}`}>
        <Icon size={18} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[10px] uppercase tracking-wider text-aegis-muted leading-tight">{label}</div>
        <motion.div
          key={value}
          initial={{ opacity: 0.3, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          className={`text-lg font-bold ${color} font-mono`}
        >
          {typeof value === 'number'
            ? value.toLocaleString('sr-RS', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
            : value}
          <span className="text-xs ml-0.5">{suffix}</span>
        </motion.div>
      </div>
    </motion.div>
  )
}
