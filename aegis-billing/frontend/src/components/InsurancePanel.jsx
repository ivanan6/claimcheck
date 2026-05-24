import { Building2, CheckCircle2, XCircle, Clock } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export default function InsurancePanel({ packet, decision }) {
  const status = !decision ? 'waiting' : decision.status

  return (
    <div className="h-full flex flex-col bg-aegis-panel/80 backdrop-blur-sm rounded-2xl border border-aegis-border p-5 overflow-hidden">
      <div className="flex items-center gap-3 mb-4 pb-3 border-b border-aegis-border">
        <div className="w-10 h-10 rounded-lg bg-aegis-success/10 flex items-center justify-center text-aegis-success">
          <Building2 size={20} />
        </div>
        <div>
          <h2 className="font-bold text-lg leading-tight">Osiguravajuca kuca</h2>
          <p className="text-xs text-aegis-muted">
            {packet?.insurance_company || 'Global Health Insurance'}
          </p>
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        <AnimatePresence mode="wait">
          {status === 'waiting' && <WaitingState key="waiting" />}
          {status === 'approved' && <ApprovedState key="approved" packet={packet} decision={decision} />}
          {status === 'rejected' && <RejectedState key="rejected" packet={packet} decision={decision} />}
        </AnimatePresence>
      </div>
    </div>
  )
}

function WaitingState() {
  return (
    <motion.div
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="flex flex-col items-center justify-center h-full text-center"
    >
      <div className="w-16 h-16 rounded-full bg-aegis-panel2 border border-aegis-border flex items-center justify-center text-aegis-muted mb-4">
        <Clock size={28} />
      </div>
      <div className="text-aegis-muted">Inbox osiguranja</div>
      <div className="text-xs text-aegis-muted/60 mt-1">Cekam novi zahtev od clearinghouse-a...</div>
    </motion.div>
  )
}

function ApprovedState({ packet, decision }) {
  const total = packet.bill_items.reduce((s, i) => s + i.unit_price_eur * i.quantity, 0)
  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex-1 flex flex-col">
      <div className="bg-aegis-success/10 border border-aegis-success/30 rounded-xl p-4 mb-4">
        <div className="flex items-center gap-3">
          <CheckCircle2 size={28} className="text-aegis-success" />
          <div>
            <div className="font-bold text-aegis-success">RACUN PRIMLJEN</div>
            <div className="text-xs text-aegis-success/80">Validacija prosla, isplata pokrenuta</div>
          </div>
        </div>
      </div>

      <div className="bg-aegis-panel2 rounded-lg border border-aegis-border p-4 space-y-3">
        <Row label="Packet ID" value={packet.packet_id} mono />
        <Row label="Klinika" value={packet.clinic_name} />
        <Row label="Pacijent" value={packet.patient.full_name} />
        <Row label="Procedure" value={packet.bill_items.map((i) => i.cpt_code).join(', ')} mono />
        <div className="pt-3 border-t border-aegis-border">
          <Row label="Iznos za isplatu" value={`${total.toFixed(2)} €`} highlight />
          <Row label="Predvidjena isplata" value="za 7-14 dana" />
        </div>
      </div>

      <div className="mt-auto pt-4 text-center">
        <div className="text-xs text-aegis-muted">
          Obradeno u {(decision.processing_time_ms / 1000).toFixed(1)}s ·
          AI validacija: <span className="text-aegis-success">PROSAO</span>
        </div>
      </div>
    </motion.div>
  )
}

function RejectedState({ packet, decision }) {
  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex-1 flex flex-col">
      <div className="bg-aegis-warning/10 border border-aegis-warning/30 rounded-xl p-4 mb-4">
        <div className="flex items-center gap-3">
          <XCircle size={28} className="text-aegis-warning" />
          <div>
            <div className="font-bold text-aegis-warning">RACUN NIJE STIGAO</div>
            <div className="text-xs text-aegis-warning/80">Zaustavljen u clearinghouse-u pre slanja</div>
          </div>
        </div>
      </div>

      <div className="bg-aegis-panel2 rounded-lg border border-aegis-border p-4">
        <div className="text-xs uppercase tracking-wider text-aegis-muted mb-2">
          Kontrast: bez AegisBilling.ai...
        </div>
        <div className="space-y-2 text-sm">
          <div className="flex gap-2 items-start">
            <span className="text-aegis-danger">✕</span>
            <span className="text-aegis-text/80">Lose pripremljen racun bi stigao do nas</span>
          </div>
          <div className="flex gap-2 items-start">
            <span className="text-aegis-danger">✕</span>
            <span className="text-aegis-text/80">Automatska odbijenica generisana za 30 dana</span>
          </div>
          <div className="flex gap-2 items-start">
            <span className="text-aegis-danger">✕</span>
            <span className="text-aegis-text/80">
              Klinika gubi <span className="font-semibold text-aegis-text">
                {decision.estimated_saved_eur.toFixed(2)} €
              </span> i pise zalbu nedelju dana
            </span>
          </div>
        </div>
        <div className="mt-3 pt-3 border-t border-aegis-border">
          <div className="text-xs text-aegis-success flex items-start gap-2">
            <CheckCircle2 size={14} className="mt-0.5 shrink-0" />
            <span>
              Aegis je zaustavio racun za <span className="font-mono">
                {(decision.processing_time_ms / 1000).toFixed(1)}s
              </span>. Sestra dobija auto-fix predlog na ekranu.
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function Row({ label, value, mono, highlight }) {
  return (
    <div className="flex justify-between items-center gap-3 text-sm">
      <span className="text-aegis-muted text-xs">{label}</span>
      <span className={`${mono ? 'font-mono text-xs' : ''} ${highlight ? 'font-bold text-aegis-success' : 'text-aegis-text'}`}>
        {value}
      </span>
    </div>
  )
}
