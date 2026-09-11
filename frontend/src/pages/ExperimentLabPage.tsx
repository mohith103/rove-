/**
 * Experiment Lab: configure and run a batch of missions, then compare agents.
 */
import { useMemo, useState } from 'react';

import AgentBar from '../components/experiments/AgentBar';
import ResultsTable from '../components/experiments/ResultsTable';
import { api } from '../services/api';
import { colors, ui } from '../theme';
import type {
  AgentName,
  Difficulty,
  ExperimentRow,
  MissionMode,
  RunExperimentResponse,
} from '../types/mission';

const ALL_AGENTS: AgentName[] = ['random', 'rule_based', 'ppo'];
const ALL_DIFFICULTIES: Difficulty[] = ['easy', 'medium', 'hard', 'extreme'];
const ALL_MODES: MissionMode[] = ['balanced', 'science', 'survival', 'exploration'];

const AGENT_COLORS: Record<string, string> = {
  random: '#7d8590',
  rule_based: '#d29922',
  ppo: '#3fb950',
};

export default function ExperimentLabPage() {
  const [agents, setAgents] = useState<AgentName[]>(['random', 'rule_based']);
  const [difficulties, setDifficulties] = useState<Difficulty[]>(['medium']);
  const [mode, setMode] = useState<MissionMode>('balanced');
  const [episodes, setEpisodes] = useState(10);
  const [seed, setSeed] = useState(42);

  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<RunExperimentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  function toggleAgent(a: AgentName) {
    setAgents((prev) =>
      prev.includes(a) ? prev.filter((x) => x !== a) : [...prev, a],
    );
  }

  function toggleDifficulty(d: Difficulty) {
    setDifficulties((prev) =>
      prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d],
    );
  }

  async function runExperiment() {
    setRunning(true);
    setError(null);
    try {
      const response = await api.runExperiment({
        agents,
        difficulties,
        mode,
        episodes,
        seed,
        max_steps: null,
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  }

  const totalMissions = agents.length * difficulties.length * episodes;

  // Per-agent aggregate across all difficulties (for bar charts)
  const agentAggregates = useMemo(() => {
    if (!result) return null;
    const byAgent = new Map<string, ExperimentRow[]>();
    for (const row of result.rows) {
      if (!byAgent.has(row.agent)) byAgent.set(row.agent, []);
      byAgent.get(row.agent)!.push(row);
    }
    return Array.from(byAgent.entries()).map(([agent, rows]) => ({
      agent,
      successRate:
        rows.reduce((s, r) => s + r.success_rate, 0) / rows.length,
      avgSamples:
        rows.reduce((s, r) => s + r.avg_samples, 0) / rows.length,
      avgEnergy:
        rows.reduce((s, r) => s + r.avg_energy_left, 0) / rows.length,
    }));
  }, [result]);

  return (
    <div className="flex flex-col gap-4">
      {/* Config panel */}
      <div className={`${ui.panel} p-6`}>
        <h2
          className="text-xs uppercase tracking-widest mb-4"
          style={{ color: colors.textDim }}
        >
          Experiment Configuration
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Agents */}
          <div>
            <div
              className="text-xs uppercase tracking-widest mb-2"
              style={{ color: colors.textDim }}
            >
              Agents
            </div>
            <div className="flex flex-wrap gap-2">
              {ALL_AGENTS.map((a) => (
                <button
                  key={a}
                  onClick={() => toggleAgent(a)}
                  className="px-3 py-1.5 rounded text-xs uppercase tracking-wider border"
                  style={{
                    backgroundColor: agents.includes(a)
                      ? `${colors.accent}22`
                      : colors.surface2,
                    borderColor: agents.includes(a)
                      ? colors.accent
                      : colors.border,
                    color: agents.includes(a) ? colors.accent : colors.text,
                  }}
                >
                  {a}
                </button>
              ))}
            </div>
          </div>

          {/* Difficulties */}
          <div>
            <div
              className="text-xs uppercase tracking-widest mb-2"
              style={{ color: colors.textDim }}
            >
              Difficulties
            </div>
            <div className="flex flex-wrap gap-2">
              {ALL_DIFFICULTIES.map((d) => (
                <button
                  key={d}
                  onClick={() => toggleDifficulty(d)}
                  className="px-3 py-1.5 rounded text-xs uppercase tracking-wider border"
                  style={{
                    backgroundColor: difficulties.includes(d)
                      ? `${colors.accent}22`
                      : colors.surface2,
                    borderColor: difficulties.includes(d)
                      ? colors.accent
                      : colors.border,
                    color: difficulties.includes(d)
                      ? colors.accent
                      : colors.text,
                  }}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>

          {/* Mode */}
          <div>
            <div
              className="text-xs uppercase tracking-widest mb-2"
              style={{ color: colors.textDim }}
            >
              Mission Mode
            </div>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value as MissionMode)}
              className="w-full px-3 py-2 rounded border bg-transparent text-sm"
              style={{
                borderColor: colors.border,
                color: colors.text,
                backgroundColor: colors.surface2,
              }}
            >
              {ALL_MODES.map((m) => (
                <option key={m} value={m} style={{ color: '#000' }}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          {/* Episodes + Seed */}
          <div>
            <div
              className="text-xs uppercase tracking-widest mb-2"
              style={{ color: colors.textDim }}
            >
              Episodes per Combination
            </div>
            <input
              type="number"
              min={1}
              max={50}
              value={episodes}
              onChange={(e) => setEpisodes(Number(e.target.value))}
              className="w-full px-3 py-2 rounded border bg-transparent mono text-sm"
              style={{ borderColor: colors.border, color: colors.text }}
            />
          </div>

          <div>
            <div
              className="text-xs uppercase tracking-widest mb-2"
              style={{ color: colors.textDim }}
            >
              Random Seed
            </div>
            <input
              type="number"
              min={0}
              value={seed}
              onChange={(e) => setSeed(Number(e.target.value))}
              className="w-full px-3 py-2 rounded border bg-transparent mono text-sm"
              style={{ borderColor: colors.border, color: colors.text }}
            />
          </div>
        </div>

        {/* Summary + Run */}
        <div
          className="mt-6 pt-4 border-t flex items-center justify-between"
          style={{ borderColor: colors.border }}
        >
          <div className="text-sm" style={{ color: colors.textDim }}>
            Will run{' '}
            <span className="mono" style={{ color: colors.accent }}>
              {totalMissions}
            </span>{' '}
            missions
          </div>
          <button
            onClick={runExperiment}
            disabled={
              running || agents.length === 0 || difficulties.length === 0
            }
            className="px-6 py-2 rounded text-sm font-medium uppercase tracking-widest transition-colors disabled:opacity-40"
            style={{ backgroundColor: colors.accent2, color: '#fff' }}
          >
            {running ? 'Running…' : 'Run Experiment'}
          </button>
        </div>

        {error && (
          <div
            className="mt-4 p-3 rounded text-sm"
            style={{
              backgroundColor: `${colors.danger}22`,
              border: `1px solid ${colors.danger}`,
              color: colors.danger,
            }}
          >
            {error}
          </div>
        )}
      </div>

      {/* Results */}
      {result && agentAggregates && (
        <>
          <div
            className="text-xs uppercase tracking-widest"
            style={{ color: colors.textDim }}
          >
            Results — {result.total_missions} missions in{' '}
            {result.elapsed_seconds.toFixed(1)}s
          </div>

          {/* Agent comparison bars */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <AgentBar
              title="Success Rate"
              rows={agentAggregates.map((a) => ({
                label: a.agent,
                value: a.successRate * 100,
                color: AGENT_COLORS[a.agent] ?? colors.accent,
              }))}
              unit="%"
              max={100}
            />
            <AgentBar
              title="Avg Samples Collected"
              rows={agentAggregates.map((a) => ({
                label: a.agent,
                value: a.avgSamples,
                color: AGENT_COLORS[a.agent] ?? colors.accent,
              }))}
            />
            <AgentBar
              title="Avg Energy Remaining"
              rows={agentAggregates.map((a) => ({
                label: a.agent,
                value: a.avgEnergy,
                color: AGENT_COLORS[a.agent] ?? colors.accent,
              }))}
              unit="%"
              max={100}
            />
          </div>

          {/* Full table */}
          <ResultsTable rows={result.rows} />
        </>
      )}
    </div>
  );
}