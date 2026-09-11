/**
 * Temporary debug page — Phase 8B.
 *
 * Creates a mission, streams live state, and dumps the raw data.
 * Will be replaced by the real Mission Control UI in Phase 8C+.
 */
import { useEffect, useState } from 'react';

import { useMissionStream } from '../hooks/useMissionStream';
import { api } from '../services/api';
import type { MissionSummary } from '../types/mission';

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between border-b border-[#1f2937] py-1">
      <span className="text-[#7d8590]">{label}</span>
      <span className="mono text-[#e6edf3]">{value}</span>
    </div>
  );
}

export default function DebugPage() {
  const [mission, setMission] = useState<MissionSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const stream = useMissionStream(mission?.id ?? null);

  // Auto-create one mission on mount (for convenience)
  useEffect(() => {
    void createMission();
    // Only run once on mount.
  }, []);

  async function createMission() {
    setLoading(true);
    setError(null);
    try {
      const summary = await api.createMission({
        difficulty: 'easy',
        agent: 'rule_based',
        mode: 'balanced',
        seed: Math.floor(Math.random() * 10000),
        speed: 5.0,
      });
      setMission(summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0e14] text-[#e6edf3] p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-widest text-[#4db8ff]">
              ROVE · DEBUG
            </h1>
            <p className="text-xs text-[#7d8590] mt-1 uppercase tracking-widest">
              Phase 8B — Backend connectivity test
            </p>
          </div>
          <button
            onClick={createMission}
            disabled={loading}
            className="px-4 py-2 rounded bg-[#1f6feb] hover:bg-[#388bfd] text-white text-sm font-medium disabled:opacity-50"
          >
            {loading ? 'Creating…' : 'New Mission'}
          </button>
        </header>

        {error && (
          <div className="p-3 rounded bg-[#3d1418] border border-[#f85149] text-[#f85149] text-sm">
            Error: {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-6">
          {/* Mission panel */}
          <section className="bg-[#11151c] rounded-lg p-4 border border-[#1f2937]">
            <h2 className="text-sm font-semibold text-[#4db8ff] uppercase tracking-wider mb-3">
              Mission
            </h2>
            {mission ? (
              <div className="space-y-1 text-sm">
                <Stat label="id" value={mission.id} />
                <Stat label="difficulty" value={mission.difficulty} />
                <Stat label="agent" value={mission.agent} />
                <Stat label="mode" value={mission.mode} />
                <Stat label="status" value={stream.status ?? mission.status} />
                <Stat
                  label="step"
                  value={`${stream.state?.step ?? mission.step} / ${mission.max_steps}`}
                />
                <Stat
                  label="connected"
                  value={stream.connected ? 'yes' : 'no'}
                />
              </div>
            ) : (
              <p className="text-[#7d8590] text-sm">No mission yet.</p>
            )}
          </section>

          {/* Rover panel */}
          <section className="bg-[#11151c] rounded-lg p-4 border border-[#1f2937]">
            <h2 className="text-sm font-semibold text-[#4db8ff] uppercase tracking-wider mb-3">
              Rover
            </h2>
            {stream.state ? (
              <div className="space-y-1 text-sm">
                <Stat label="position" value={`(${stream.state.rover.x}, ${stream.state.rover.y})`} />
                <Stat label="energy" value={`${stream.state.rover.energy.toFixed(1)}%`} />
                <Stat label="oxygen" value={`${stream.state.rover.oxygen.toFixed(1)}%`} />
                <Stat label="water" value={`${stream.state.rover.water.toFixed(1)}%`} />
                <Stat label="health" value={`${stream.state.rover.rover_health.toFixed(1)}%`} />
                <Stat label="samples" value={stream.state.rover.samples_collected} />
              </div>
            ) : (
              <p className="text-[#7d8590] text-sm">Waiting for stream…</p>
            )}
          </section>

          {/* Decision panel */}
          <section className="col-span-2 bg-[#11151c] rounded-lg p-4 border border-[#1f2937]">
            <h2 className="text-sm font-semibold text-[#4db8ff] uppercase tracking-wider mb-3">
              Latest AI Decision
            </h2>
            {stream.decision ? (
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-3">
                  <span className="px-2 py-0.5 rounded bg-[#1f6feb] text-white text-xs font-mono">
                    {stream.decision.explanation.action_name}
                  </span>
                  <span className="text-[#7d8590] text-xs">
                    confidence {stream.decision.explanation.confidence.toFixed(2)} ·
                    risk {stream.decision.explanation.risk_estimate.toFixed(2)}
                  </span>
                  {stream.decision.overridden_by_planner && (
                    <span className="px-2 py-0.5 rounded bg-[#d29922] text-black text-xs">
                      OVERRIDDEN
                    </span>
                  )}
                </div>
                <p className="text-[#e6edf3]">{stream.decision.explanation.reason}</p>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  {Object.entries(stream.decision.explanation.factors).map(([k, v]) => (
                    <div key={k} className="text-xs flex justify-between border-b border-[#1f2937] py-0.5">
                      <span className="text-[#7d8590]">{k}</span>
                      <span className="mono">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-[#7d8590] text-sm">No decision yet.</p>
            )}
          </section>

          {/* Event log */}
          <section className="col-span-2 bg-[#11151c] rounded-lg p-4 border border-[#1f2937] max-h-64 overflow-y-auto">
            <h2 className="text-sm font-semibold text-[#4db8ff] uppercase tracking-wider mb-3">
              Event Log
            </h2>
            {stream.state?.events?.length ? (
              <ul className="text-xs mono space-y-0.5">
                {stream.state.events.slice(-15).map((e, i) => (
                  <li key={i} className="text-[#8b949e]">{e}</li>
                ))}
              </ul>
            ) : (
              <p className="text-[#7d8590] text-sm">No events yet.</p>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}