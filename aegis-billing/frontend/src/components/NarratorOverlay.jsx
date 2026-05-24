import { AnimatePresence, motion } from 'framer-motion'

export default function NarratorOverlay({ step, stepNumber }) {
  return (
    <AnimatePresence mode="wait">
      {step && (
        <motion.div
          key={step}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.3 }}
          className="fixed bottom-10 left-1/2 -translate-x-1/2 z-40 pointer-events-none"
        >
          <div className="bg-aegis-primary text-white rounded-full pl-2 pr-5 py-2 shadow-aegis-card-hover flex items-center gap-3">
            {stepNumber !== undefined && stepNumber > 0 && (
              <div className="w-7 h-7 rounded-full bg-aegis-accent text-white font-bold text-xs flex items-center justify-center font-mono">
                {stepNumber}
              </div>
            )}
            <div className="text-sm font-medium">{step}</div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
