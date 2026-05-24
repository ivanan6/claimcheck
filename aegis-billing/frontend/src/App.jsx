import { useEffect, useState, useCallback, useRef } from 'react'
import { Shield, Zap } from 'lucide-react'

import ClinicPanel from './components/ClinicPanel'
import ClearinghousePanel from './components/ClearinghousePanel'
import InsurancePanel from './components/InsurancePanel'
import PipelineAnimation from './components/PipelineAnimation'
import StatsDashboard from './components/StatsDashboard'
import NarratorOverlay from './components/NarratorOverlay'
import AegisFixModal from './components/AegisFixModal'
import ScenarioSelector from './components/ScenarioSelector'

import {
  listScenarios, getScenario, streamIntercept, applyFix, recordStats, getStats,
} from './lib/api'

const STAGE_NARRATIVE = {
  clearinghouse_received: { text: 'EDI 837 paket usao u clearinghouse', stepNumber: 1, pipeline: 'to_clearinghouse' },
  agent1_started: { text: 'Agent 1 cita slobodan tekst lekara (Gemini)...', stepNumber: 2, pipeline: 'in_clearinghouse' },
  agent1_done: { text: 'Agent 1 izvukao klinicke nalaze i ICD-10 sifre', stepNumber: 2, pipeline: 'in_clearinghouse' },
  agent2_started: { text: 'Agent 2 pretrazuje ugovor osiguranja (Graph RAG)', stepNumber: 3, pipeline: 'in_clearinghouse' },
  agent2_done: { text: 'Agent 2 izvukao pravila iz ugovora', stepNumber: 3, pipeline: 'in_clearinghouse' },
  agent3_started: { text: 'Agent 3 unakrsno proverava racun...', stepNumber: 4, pipeline: 'in_clearinghouse' },
  agent3_done: { text: 'Agent 3 donosi odluku', stepNumber: 4, pipeline: 'in_clearinghouse' },
  delivered_to_insurance: { text: 'Racun isporucen osiguranju', stepNumber: 5, pipeline: 'to_insurance' },
  blocked_by_aegis: { text: 'STOP! Aegis je zaustavio lose pripremljen racun.', stepNumber: 5, pipeline: 'blocked' },
}

export default function App() {
  const [scenarios, setScenarios] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [packet, setPacket] = useState(null)
  const [running, setRunning] = useState(false)

  const [agentStates, setAgentStates] = useState({ 1: 'idle', 2: 'idle', 3: 'idle' })
  const [agentResults, setAgentResults] = useState({ 1: null, 2: null, 3: null })
  const [decision, setDecision] = useState(null)

  const [narrator, setNarrator] = useState(null)
  const [pipelineStage, setPipelineStage] = useState('idle')

  const [fixModalOpen, setFixModalOpen] = useState(false)
  const [fixBusy, setFixBusy] = useState(false)

  const [stats, setStats] = useState(null)
  const closeStreamRef = useRef(null)

  useEffect(() => {
    listScenarios().then(setScenarios).catch(console.error)
    getStats().then(setStats).catch(() => {})
  }, [])

  const handleSelect = useCallback(async (id) => {
    setSelectedId(id)
    setDecision(null)
    setAgentStates({ 1: 'idle', 2: 'idle', 3: 'idle' })
    setAgentResults({ 1: null, 2: null, 3: null })
    setPipelineStage('idle')
    setNarrator(null)
    try {
      const p = await getScenario(id)
      setPacket(p)
    } catch (e) { console.error(e) }
  }, [])

  const handleRun = useCallback(() => {
    if (!selectedId) return
    setRunning(true)
    setDecision(null)
    setAgentStates({ 1: 'idle', 2: 'idle', 3: 'idle' })
    setAgentResults({ 1: null, 2: null, 3: null })
    setPipelineStage('to_clearinghouse')
    setNarrator({ text: 'Pokrecem demo...', stepNumber: 0 })

    closeStreamRef.current = streamIntercept(selectedId, {
      onStage: (data) => {
        const meta = STAGE_NARRATIVE[data.stage]
        if (meta) {
          setNarrator({ text: meta.text, stepNumber: meta.stepNumber })
          setPipelineStage(meta.pipeline)
        }
        if (data.stage === 'agent1_started') setAgentStates((s) => ({ ...s, 1: 'running' }))
        if (data.stage === 'agent1_done') setAgentStates((s) => ({ ...s, 1: 'done' }))
        if (data.stage === 'agent2_started') setAgentStates((s) => ({ ...s, 2: 'running' }))
        if (data.stage === 'agent2_done') setAgentStates((s) => ({ ...s, 2: 'done' }))
        if (data.stage === 'agent3_started') setAgentStates((s) => ({ ...s, 3: 'running' }))
      },
      onAgentResult: (data) => {
        const num = data.agent_number
        if (num === 1) setAgentResults((r) => ({ ...r, 1: data.findings }))
        else if (num === 2) setAgentResults((r) => ({ ...r, 2: data.rules }))
        else if (num === 3) {
          setAgentResults((r) => ({ ...r, 3: data.issues }))
          const hasErrors = (data.issues || []).some((i) => i.severity === 'error')
          setAgentStates((s) => ({ ...s, 3: hasErrors ? 'flagged' : 'done' }))
        }
      },
      onDecision: (data) => {
        setDecision(data)
        recordStats(data).then(setStats).catch(() => {})
        if (data.status === 'rejected') {
          setTimeout(() => setFixModalOpen(true), 1200)
        }
      },
      onDone: () => {
        setRunning(false)
        closeStreamRef.current = null
      },
      onError: (e) => {
        console.error('SSE greska', e)
        setRunning(false)
        setNarrator({
          text: 'Greska pri komunikaciji sa backendom. Proveri GEMINI_API_KEY u .env.',
          stepNumber: 0,
        })
      },
    })
  }, [selectedId])

  const handleApplyFix = useCallback(async (fixes) => {
    if (!selectedId) return
    setFixBusy(true)
    try {
      const newDecision = await applyFix(selectedId, fixes)
      setPacket((prev) => {
        if (!prev) return prev
        const updated = { ...prev, bill_items: prev.bill_items.map((b) => ({ ...b })) }
        for (const f of fixes) {
          if (f.action === 'add_icd10') {
            const target = f.to_cpt || f.cpt
            const it = updated.bill_items.find((b) => b.cpt_code === target)
            if (it) for (const c of f.codes || []) if (!it.icd10_codes.includes(c)) it.icd10_codes.push(c)
          }
        }
        return updated
      })

      setDecision(newDecision)
      setAgentResults({
        1: newDecision.agent1_findings,
        2: newDecision.agent2_rules,
        3: newDecision.agent3_issues,
      })
      const hasErrorsNow = newDecision.agent3_issues.some((i) => i.severity === 'error')
      setAgentStates({ 1: 'done', 2: 'done', 3: hasErrorsNow ? 'flagged' : 'done' })

      if (newDecision.status === 'approved') {
        setPipelineStage('to_insurance')
        setNarrator({ text: 'Posle 1-click fix-a: racun prosao!', stepNumber: 6 })
      }
      recordStats(newDecision).then(setStats).catch(() => {})
      setFixModalOpen(false)
    } catch (e) {
      console.error(e)
    } finally {
      setFixBusy(false)
    }
  }, [selectedId])

  return (
    <div className="min-h-screen flex flex-col p-5 gap-4">
      <header className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-aegis-accent to-aegis-accent2 flex items-center justify-center shadow-lg shadow-aegis-accent/20">
            <Shield size={22} className="text-aegis-bg" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">
              AegisBilling.<span className="text-aegis-accent">ai</span>
            </h1>
            <p className="text-xs text-aegis-muted -mt-0.5">
              <Zap size={10} className="inline mr-1 -mt-0.5" />
              AI filter izmedju klinike i osiguranja · Gemini powered
            </p>
          </div>
        </div>

        <ScenarioSelector
          scenarios={scenarios}
          selectedId={selectedId}
          onSelect={handleSelect}
          onRun={handleRun}
          running={running}
        />
      </header>

      <StatsDashboard stats={stats} />
      <PipelineAnimation activeStage={pipelineStage} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1 min-h-[600px]">
        <ClinicPanel
          packet={packet}
          highlightMissingIcd10={running && packet?.bill_items?.some((b) => b.icd10_codes.length === 0)}
        />
        <ClearinghousePanel agentStates={agentStates} agentResults={agentResults} decision={decision} />
        <InsurancePanel packet={packet} decision={decision} />
      </div>

      <NarratorOverlay step={narrator?.text} stepNumber={narrator?.stepNumber} />

      <AegisFixModal
        open={fixModalOpen}
        issues={agentResults[3]}
        findings={agentResults[1]}
        onApply={handleApplyFix}
        onClose={() => setFixModalOpen(false)}
        busy={fixBusy}
      />

      <footer className="text-center text-[11px] text-aegis-muted/60 mt-2">
        AegisBilling.ai · Multi-Agent + Graph RAG · Backend Python/FastAPI · Frontend React/Vite · LLM: Google Gemini
      </footer>
    </div>
  )
}
