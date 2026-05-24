import { motion } from 'framer-motion'

export default function PipelineAnimation({ activeStage = 'idle' }) {
  const positions = {
    idle: { x: '8%', color: '#252b3d', pulse: false },
    to_clearinghouse: { x: '50%', color: '#00d4ff', pulse: false },
    in_clearinghouse: { x: '50%', color: '#7c3aed', pulse: true },
    to_insurance: { x: '92%', color: '#10b981', pulse: false },
    blocked: { x: '8%', color: '#ef4444', pulse: true },
  }

  const cur = positions[activeStage] || positions.idle

  return (
    <div className="relative w-full h-16 flex items-center pointer-events-none">
      <div className="absolute left-0 right-0 h-px bg-aegis-border" />
      <div
        className={`pipeline-line absolute left-0 right-0 h-px ${
          activeStage !== 'idle' && activeStage !== 'blocked' ? 'active' : ''
        }`}
        style={{ opacity: activeStage === 'idle' ? 0.2 : 0.8 }}
      />

      {[
        { left: '8%', label: 'Klinika' },
        { left: '50%', label: 'Aegis' },
        { left: '92%', label: 'Osig.' },
      ].map((m) => (
        <div key={m.left} className="absolute" style={{ left: m.left, transform: 'translateX(-50%)' }}>
          <div className="w-3 h-3 rounded-full bg-aegis-panel border-2 border-aegis-border" />
          <div className="absolute top-5 left-1/2 -translate-x-1/2 text-[9px] uppercase tracking-wider text-aegis-muted whitespace-nowrap">
            {m.label}
          </div>
        </div>
      ))}

      <motion.div
        className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2"
        animate={{ left: cur.x }}
        transition={{ duration: 1.2, ease: 'easeInOut' }}
      >
        <motion.div
          className="packet-dot"
          animate={{
            scale: cur.pulse ? [1, 1.4, 1] : 1,
            backgroundColor: cur.color,
            boxShadow: `0 0 20px ${cur.color}, 0 0 40px ${cur.color}88`,
          }}
          transition={{
            scale: { duration: 0.9, repeat: cur.pulse ? Infinity : 0 },
            backgroundColor: { duration: 0.4 },
          }}
        />
      </motion.div>
    </div>
  )
}
