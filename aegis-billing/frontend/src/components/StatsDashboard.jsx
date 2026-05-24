import { TrendingUp, ShieldOff, Activity, Timer } from 'lucide-react'
import { motion } from 'framer-motion'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'

export default function StatsDashboard({ stats }) {
  if (!stats) stats = { total_intercepted: 0, errors_blocked: 0, saved_eur: 0, avg_processing_ms: 0 }

  const items = [
    {
      icon: Activity,
      label: 'Bills intercepted',
      value: stats.total_intercepted,
      suffix: '',
      tint: 'primary',
    },
    {
      icon: ShieldOff,
      label: 'Errors blocked',
      value: stats.errors_blocked,
      suffix: '',
      tint: 'danger',
    },
    {
      icon: TrendingUp,
      label: 'Saved for clinics',
      value: stats.saved_eur,
      suffix: ' €',
      decimals: 2,
      tint: 'success',
    },
    {
      icon: Timer,
      label: 'Avg processing',
      value: stats.avg_processing_ms / 1000,
      suffix: 's',
      decimals: 1,
      tint: 'accent',
    },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {items.map((it, i) => <StatCard key={i} {...it} />)}
    </div>
  )
}

const TINTS = {
  primary: { iconBg: 'bg-primary/10', iconText: 'text-primary', value: 'text-primary' },
  accent: { iconBg: 'bg-accent/10', iconText: 'text-accent', value: 'text-accent' },
  danger: { iconBg: 'bg-aegis-danger-soft', iconText: 'text-aegis-danger', value: 'text-aegis-danger' },
  success: { iconBg: 'bg-aegis-success-soft', iconText: 'text-aegis-success', value: 'text-aegis-success' },
}

function StatCard({ icon: Icon, label, value, suffix, decimals = 0, tint = 'primary' }) {
  const t = TINTS[tint]
  return (
    <Card className="p-5 flex items-start gap-4 hover:shadow-md transition-shadow">
      <div className={cn('w-11 h-11 rounded-xl flex items-center justify-center shrink-0', t.iconBg, t.iconText)}>
        <Icon size={20} strokeWidth={2.2} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-semibold leading-tight">
          {label}
        </div>
        <motion.div
          key={value}
          initial={{ opacity: 0.4, y: -3 }}
          animate={{ opacity: 1, y: 0 }}
          className={cn('text-2xl font-bold mt-1 font-mono tabular-nums leading-none', t.value)}
        >
          {typeof value === 'number'
            ? value.toLocaleString('en-US', {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals,
              })
            : value}
          <span className="text-base ml-0.5 font-semibold">{suffix}</span>
        </motion.div>
      </div>
    </Card>
  )
}
