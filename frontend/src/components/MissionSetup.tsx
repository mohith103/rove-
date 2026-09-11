/**
 * Pre-mission configuration screen.
 */
import { useState } from 'react';

import { colors, ui } from '../theme';
import type {
  AgentName,
  Difficulty,
  MissionMode,
} from '../types/mission';

interface Props {
  onLaunch: (config: {
    difficulty: Difficulty;
    agent: AgentName;
    mode: MissionMode;
    seed: number;
    speed: number;
    max_steps?: number | null;
    map_size?: number | null;
    multi_agent?: boolean;
  }) => void;
  loading?: boolean;
  error?: string | null;
}

interface OptionDef<T extends string> {
  value: T;
  label: string;
  description: string;
}

const DIFFICULTIES: OptionDef<Difficulty>[] = [
  { value: 'easy', label: 'Easy', description: 'Calm weather, rare failures, longer mission' },
  { value: 'medium', label: 'Medium', description: 'Random weather, occasional failures' },
  { value: 'hard', label: 'Hard', description: 'Frequent storms, equipment damage' },
  { value: 'extreme', label: 'Extreme', description: 'Severe weather, high failure rate' },
];

const AGENTS: OptionDef<AgentName>[] = [
  { value: 'rule_based', label: 'Rule-Based', description: 'Hand-crafted IF-THEN commander' },
  { value: 'ppo', label: 'PPO', description: 'Reinforcement-learning agent' },
  { value: 'random', label: 'Random', description: 'Baseline — picks actions randomly' },
];

const MODES: OptionDef<MissionMode>[] = [
  { value: 'balanced', label: 'Balanced', description: 'Mix of science, safety, and efficiency' },
  { value: 'science', label: 'Science', description: 'Prioritize sample collection' },
  { value: 'survival', label: 'Survival', description: 'Prioritize rover safety and resources' },
  { value: 'exploration', label: 'Exploration', description: 'Prioritize visiting new areas' },
];

function OptionGroup<T extends string>({
  title, options, value, onChange,
}: {
  title: string;
  options: OptionDef<T>[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div>
      <h3 className="text-xs uppercase tracking-widest mb-2" style={{ color: colors.textDim }}>
        {title}
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {options.map((opt) => {
          const selected = value === opt.value;
          return (
            <button
              key={opt.value}
              onClick={() => onChange(opt.value)}
              className="text-left p-3 rounded border transition-colors"
              style={{
                backgroundColor: selected ? `${colors.accent}22` : colors.surface,
                borderColor: selected ? colors.accent : colors.border,
                color: colors.text,
              }}
            >
              <div className="text-sm font-medium mb-1" style={{ color: selected ? colors.accent : colors.text }}>
                {opt.label}
              </div>
              <div className="text-xs leading-snug" style={{ color: colors.textDim }}>
                {opt.description}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function MissionSetup({ onLaunch, loading = false, error }: Props) {
  const [difficulty, setDifficulty] = useState<Difficulty>('medium');
  const [agent, setAgent] = useState<AgentName>('rule_based');
  const [mode, setMode] = useState<MissionMode>('balanced');
  const [speed, setSpeed] = useState(3);
  const [seed, setSeed] = useState<number>(() => Math.floor(Math.random() * 10000));
  const [multiAgent, setMultiAgent] = useState(false);

  function handleLaunch() {
    onLaunch({
      difficulty,
      agent,
      mode,
      seed,
      speed,
      multi_agent: multiAgent,
    });
  }

  function regenerateSeed() {
    setSeed(Math.floor(Math.random() * 10000));
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6" style={{ backgroundColor: colors.bg }}>
      <div className={`${ui.panel} w-full max-w-4xl p-8`}>
        <div className="mb-8">
          <h1 className="text-4xl font-bold tracking-[0.25em] mb-2" style={{ color: colors.accent }}>
            ROVE
          </h1>
          <p className="text-sm uppercase tracking-widest" style={{ color: colors.textDim }}>
            Configure Mission
          </p>
        </div>

        <div className="space-y-6">
          <OptionGroup title="Difficulty" options={DIFFICULTIES} value={difficulty} onChange={setDifficulty} />
          <OptionGroup title="Agent" options={AGENTS} value={agent} onChange={setAgent} />
          <OptionGroup title="Mission Mode" options={MODES} value={mode} onChange={setMode} />

          {/* Commander Architecture */}
          <div>
            <h3 className="text-xs uppercase tracking-widest mb-2" style={{ color: colors.textDim }}>
              Commander Architecture
            </h3>
            <div className="flex gap-2">
              <button
                onClick={() => setMultiAgent(false)}
                className="px-4 py-2 rounded text-xs uppercase tracking-wider border"
                style={{
                  backgroundColor: !multiAgent ? `${colors.accent}22` : colors.surface,
                  borderColor: !multiAgent ? colors.accent : colors.border,
                  color: !multiAgent ? colors.accent : colors.text,
                }}
              >
                Single Agent
              </button>
              <button
                onClick={() => setMultiAgent(true)}
                className="px-4 py-2 rounded text-xs uppercase tracking-wider border"
                style={{
                  backgroundColor: multiAgent ? `${colors.accent}22` : colors.surface,
                  borderColor: multiAgent ? colors.accent : colors.border,
                  color: multiAgent ? colors.accent : colors.text,
                }}
              >
                Multi-Agent (4 specialists)
              </button>
            </div>
            <p className="text-xs mt-2" style={{ color: colors.textMuted }}>
              {multiAgent
                ? 'Navigation, Science, Safety, and Resource specialists vote on every action.'
                : 'A single commander decides using policy + planner + explainer.'}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-xs uppercase tracking-widest mb-2" style={{ color: colors.textDim }}>
                Simulation Speed
              </h3>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min={1}
                  max={10}
                  step={1}
                  value={speed}
                  onChange={(e) => setSpeed(Number(e.target.value))}
                  className="flex-1"
                />
                <span className="mono text-lg w-12 text-center" style={{ color: colors.accent }}>
                  {speed}×
                </span>
              </div>
            </div>

            <div>
              <h3 className="text-xs uppercase tracking-widest mb-2" style={{ color: colors.textDim }}>
                Random Seed
              </h3>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={seed}
                  onChange={(e) => setSeed(Number(e.target.value))}
                  className="flex-1 px-3 py-2 rounded border bg-transparent mono text-sm"
                  style={{ borderColor: colors.border, color: colors.text }}
                />
                <button
                  onClick={regenerateSeed}
                  className="px-3 py-2 rounded text-xs uppercase"
                  style={{ backgroundColor: colors.surface2, color: colors.textDim }}
                >
                  ⟳
                </button>
              </div>
            </div>
          </div>
        </div>

        {error && (
          <div
            className="mt-6 p-3 rounded text-sm"
            style={{
              backgroundColor: `${colors.danger}22`,
              border: `1px solid ${colors.danger}`,
              color: colors.danger,
            }}
          >
            {error}
          </div>
        )}

        <div className="mt-8 flex justify-end">
          <button
            onClick={handleLaunch}
            disabled={loading}
            className="px-6 py-3 rounded text-sm font-medium uppercase tracking-widest transition-colors disabled:opacity-50"
            style={{ backgroundColor: colors.accent2, color: '#fff' }}
          >
            {loading ? 'Launching…' : 'Launch Mission'}
          </button>
        </div>
      </div>
    </div>
  );
}
