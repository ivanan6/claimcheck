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
          className="fixed top-20 left-1/2 -translate-x-1/2 z-40 pointer-events-none"
        >
          <div className="bg-aegis-bg/95 backdrop-blur-md border border-aegis-accent/50 rounded-full px-5 py-2.5 shadow-2xl shadow-aegis-accent/20">
            <div className="flex items-center gap-3">
              {stepNumber !== undefined && (
                <div className="w-7 h-7 rounded-full bg-aegis-accent text-aegis-bg font-bold text-xs flex items-center justify-center">
                  {stepNumber}
                </div>
              )}
              <div className="text-sm font-medium text-aegis-text">{step}</div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
