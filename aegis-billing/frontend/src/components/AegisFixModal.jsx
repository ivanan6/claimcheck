import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle, Sparkles, X } from 'lucide-react'

export default function AegisFixModal({ open, issues, findings, onApply, onClose, busy }) {
  const proposedFixes = (issues || [])
    .filter((i) => i.severity === 'error')
    .map((i) => {
      let fix = i.suggested_fix || {}
      if (
        (i.issue_type === 'missing_icd10_justification' || i.issue_type === 'icd10_procedure_mismatch') &&
        (!fix.codes || fix.codes.length === 0) &&
        findings?.length > 0
      ) {
        fix = {
          ...fix,
          action: 'add_icd10',
          codes: findings.slice(0, 1).map((f) => f.suggested_icd10),
          to_cpt: i.line_item_cpt,
        }
      }
      return { issue: i, fix }
    })

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[92%] max-w-xl"
          >
            <div className="bg-aegis-panel border-2 border-aegis-danger/60 rounded-2xl shadow-2xl shadow-aegis-danger/30 overflow-hidden">
              <div className="bg-aegis-danger/15 border-b border-aegis-danger/40 px-5 py-3 flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-aegis-danger flex items-center justify-center text-white">
                  <AlertTriangle size={20} />
                </div>
                <div className="flex-1">
                  <div className="font-bold text-aegis-danger">
                    AEGIS UPOZORENJE - Racun ne moze biti poslat
                  </div>
                  <div className="text-xs text-aegis-text/80">
                    AI je presreo {proposedFixes.length} gresaka pre slanja osiguranju
                  </div>
                </div>
                <button onClick={onClose} className="text-aegis-muted hover:text-aegis-text transition">
                  <X size={18} />
                </button>
              </div>

              <div className="p-5 space-y-4 max-h-[60vh] overflow-y-auto">
                {proposedFixes.length === 0 && (
                  <div className="text-sm text-aegis-muted text-center py-6">
                    Nije moguce automatski generisati ispravku za ove greske.
                    <br />Potrebna je rucna intervencija lekara.
                  </div>
                )}

                {proposedFixes.map(({ issue, fix }, idx) => (
                  <div key={idx} className="bg-aegis-panel2 rounded-lg border border-aegis-border p-4">
                    <div className="flex items-start gap-3">
                      <div className="w-7 h-7 rounded-full bg-aegis-danger/20 text-aegis-danger flex items-center justify-center text-xs font-bold shrink-0">
                        {idx + 1}
                      </div>
                      <div className="flex-1">
                        <div className="text-sm font-semibold text-aegis-text">{issue.explanation}</div>
                        <div className="text-xs text-aegis-muted mt-0.5 font-mono">
                          CPT {issue.line_item_cpt} · {issue.issue_type.replace(/_/g, ' ')}
                        </div>

                        {fix.action === 'add_icd10' && fix.codes?.length > 0 && (
                          <div className="mt-3 bg-aegis-accent/5 border border-aegis-accent/30 rounded p-3">
                            <div className="text-[10px] uppercase tracking-wider text-aegis-accent mb-1.5 flex items-center gap-1">
                              <Sparkles size={11} /> Predlog AI agenta
                            </div>
                            <div className="text-sm">
                              Dodati ICD-10 sifru{' '}
                              {fix.codes.map((c) => (
                                <span key={c} className="inline-block font-mono font-bold bg-aegis-accent/20 text-aegis-accent px-1.5 py-0.5 rounded mx-0.5">
                                  {c}
                                </span>
                              ))}{' '}
                              uz proceduru CPT <span className="font-mono">{fix.to_cpt}</span>
                            </div>
                          </div>
                        )}

                        {fix.action && fix.action !== 'add_icd10' && (
                          <div className="mt-3 text-xs text-aegis-muted italic">
                            {fix.details || JSON.stringify(fix)}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="bg-aegis-bg/50 border-t border-aegis-border p-4 flex gap-3">
                <button
                  onClick={onClose}
                  disabled={busy}
                  className="px-4 py-2.5 rounded-lg text-sm text-aegis-muted hover:text-aegis-text transition disabled:opacity-40"
                >
                  Odbaci
                </button>
                <button
                  onClick={() => onApply(proposedFixes.map((p) => p.fix))}
                  disabled={busy || proposedFixes.length === 0 || !proposedFixes.some(p => p.fix.action === 'add_icd10')}
                  className="flex-1 px-4 py-2.5 rounded-lg bg-aegis-accent text-aegis-bg font-bold hover:bg-aegis-accent/90 transition flex items-center justify-center gap-2 disabled:opacity-40"
                >
                  <Sparkles size={16} />
                  {busy ? 'Primenjujem ispravke...' : '1-Click Auto-Dopuna i ponovo posalji'}
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
