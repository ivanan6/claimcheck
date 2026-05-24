import { Stethoscope, FileText, Receipt, AlertCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export default function ClinicPanel({ packet, highlightMissingIcd10 = false }) {
  if (!packet) {
    return (
      <PanelShell icon={Stethoscope} title="Klinika" subtitle="Cekanje paketa...">
        <div className="text-aegis-muted text-sm">Izaberite scenario gore.</div>
      </PanelShell>
    )
  }

  return (
    <PanelShell icon={Stethoscope} title="Klinika" subtitle={packet.clinic_name}>
      <div className="bg-aegis-panel2 rounded-lg p-3 mb-4 border border-aegis-border">
        <div className="text-xs uppercase tracking-wider text-aegis-muted mb-1">Pacijent</div>
        <div className="font-semibold">{packet.patient.full_name}</div>
        <div className="text-xs text-aegis-muted font-mono mt-1">
          {packet.patient.patient_id} · {packet.patient.date_of_birth}
        </div>
      </div>

      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2">
          <FileText size={14} className="text-aegis-accent" />
          <span className="text-xs uppercase tracking-wider text-aegis-muted">
            Lekarski nalaz (slobodan tekst)
          </span>
        </div>
        <div className="bg-aegis-panel2 rounded-lg p-3 border border-aegis-border text-sm leading-relaxed italic text-aegis-text/90">
          "{packet.doctor_note}"
        </div>
      </div>

      <div className="mb-2">
        <div className="flex items-center gap-2 mb-2">
          <Receipt size={14} className="text-aegis-accent" />
          <span className="text-xs uppercase tracking-wider text-aegis-muted">
            Racun (uneo administracija)
          </span>
        </div>
        <div className="space-y-2">
          <AnimatePresence>
            {packet.bill_items.map((item, idx) => (
              <motion.div
                key={item.cpt_code + idx}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-aegis-panel2 rounded-lg p-3 border border-aegis-border"
              >
                <div className="flex justify-between items-start gap-2">
                  <div className="flex-1">
                    <div className="font-mono text-xs text-aegis-accent">CPT {item.cpt_code}</div>
                    <div className="text-sm font-medium mt-0.5">{item.description}</div>
                  </div>
                  <div className="text-right text-sm">
                    <div className="font-semibold">{item.unit_price_eur.toFixed(2)} €</div>
                    <div className="text-xs text-aegis-muted">x{item.quantity}</div>
                  </div>
                </div>

                <div className="mt-2 pt-2 border-t border-aegis-border/50">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[10px] uppercase tracking-wider text-aegis-muted">
                      ICD-10:
                    </span>
                    {item.icd10_codes.length === 0 ? (
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-mono ${
                          highlightMissingIcd10
                            ? 'bg-aegis-danger/20 text-aegis-danger border border-aegis-danger/50 animate-pulse'
                            : 'bg-aegis-border text-aegis-muted'
                        }`}
                      >
                        {highlightMissingIcd10 && <AlertCircle size={10} className="inline mr-1" />}
                        NEDOSTAJE
                      </span>
                    ) : (
                      item.icd10_codes.map((c) => (
                        <span
                          key={c}
                          className="text-xs px-2 py-0.5 rounded font-mono bg-aegis-accent/10 text-aegis-accent border border-aegis-accent/30"
                        >
                          {c}
                        </span>
                      ))
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-aegis-border flex justify-between items-center">
        <div className="text-xs font-mono text-aegis-muted">{packet.packet_id}</div>
        <div className="text-sm">
          <span className="text-aegis-muted">Ukupno:</span>{' '}
          <span className="font-bold text-aegis-text">
            {packet.bill_items.reduce((s, i) => s + i.unit_price_eur * i.quantity, 0).toFixed(2)} €
          </span>
        </div>
      </div>
    </PanelShell>
  )
}

function PanelShell({ icon: Icon, title, subtitle, children }) {
  return (
    <div className="h-full flex flex-col bg-aegis-panel/80 backdrop-blur-sm rounded-2xl border border-aegis-border p-5 overflow-hidden">
      <div className="flex items-center gap-3 mb-4 pb-3 border-b border-aegis-border">
        <div className="w-10 h-10 rounded-lg bg-aegis-accent/10 flex items-center justify-center text-aegis-accent">
          <Icon size={20} />
        </div>
        <div>
          <h2 className="font-bold text-lg leading-tight">{title}</h2>
          <p className="text-xs text-aegis-muted">{subtitle}</p>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto pr-1">{children}</div>
    </div>
  )
}
