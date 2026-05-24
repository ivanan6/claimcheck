import { motion } from 'framer-motion'
import { Building2, ShieldCheck, Landmark } from 'lucide-react'

export default function PipelineAnimation({ activeStage = 'idle' }) {
  const positions = {
    idle: { x: '8%', color: '#cdd5e0', pulse: false },
    to_clearinghouse: { x: '50%', color: '#f97316', pulse: false },
    in_clearinghouse: { x: '50%', color: '#0b1f4d', pulse: true },
    to_insurance: { x: '92%', color: '#0b8a4a', pulse: false },
    blocked: { x: '8%', color: '#dc2626', pulse: true },
  }

  const cur = positions[activeStage] || positions.idle

  const milestones = [
    { left: '8%', label: 'Clinic', icon: Building2 },
    { left: '50%', label: 'Aegis · Clearinghouse', icon: ShieldCheck },
    { left: '92%', label: 'Insurance', icon: Landmark },
  ]

  return (
    <div className="relative w-full h-20 flex items-center pointer-events-none">
      {/* Static line */}
      <div className="absolute left-0 right-0 h-px bg-aegis-border" />

      {/* Animated overlay */}
      <div
        className={`pipeline-line absolute left-0 right-0 h-px ${
          activeStage !== 'idle' && activeStage !== 'blocked' ? 'active' : ''
        }`}
        style={{ opacity: activeStage === 'idle' ? 0 : 1 }}
      />

      {/* Milestones */}
      {milestones.map((m) => {
        const Icon = m.icon
        return (
          <div
            key={m.left}
            className="absolute"
            style={{ left: m.left, transform: 'translateX(-50%)' }}
          >
            <div className="w-9 h-9 rounded-full bg-aegis-panel border border-aegis-border-strong flex items-center justify-center text-aegis-primary shadow-aegis-card">
              <Icon size={16} strokeWidth={2.2} />
            </div>
            <div className="absolute top-11 left-1/2 -translate-x-1/2 text-[10px] font-semibold uppercase tracking-wider text-aegis-muted whitespace-nowrap">
              {m.label}
            </div>
          </div>
        )
      })}

      {/* Traveling packet dot */}
      <motion.div
        className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2"
        animate={{ left: cur.x }}
        transition={{ duration: 1.2, ease: 'easeInOut' }}
      >
        <motion.div
          className="rounded-full"
          style={{ width: 14, height: 14 }}
          animate={{
            scale: cur.pulse ? [1, 1.35, 1] : 1,
            backgroundColor: cur.color,
            boxShadow: `0 0 0 6px ${cur.color}22, 0 2px 8px -2px ${cur.color}66`,
          }}
          transition={{
            scale: { duration: 1.0, repeat: cur.pulse ? Infinity : 0 },
            backgroundColor: { duration: 0.4 },
          }}
        />
      </motion.div>
    </div>
  )
}
