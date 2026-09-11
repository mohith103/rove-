/**
 * Mission control top bar: title, SOL counter, connection status,
 * mission status, pause/resume controls, and New Mission button.
 */
import { colors } from '../theme';

interface TopBarProps {
  sol: number;
  maxSol: number;
  connected: boolean;
  status: 'running' | 'paused' | 'done' | null;
  agentName: string;
  difficulty: string;
  speed: number;
  onPause: () => void;
  onResume: () => void;
  onNewMission: () => void;
}

function StatusDot({ connected }: { connected: boolean }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span
        className="w-2 h-2 rounded-full animate-pulse"
        style={{
          backgroundColor: connected ? colors.success : colors.danger,
          boxShadow: `0 0 6px ${connected ? colors.success : colors.danger}`,
        }}
      />
      <span className="text-xs mono" style={{ color: colors.textDim }}>
        {connected ? 'LIVE' : 'OFFLINE'}
      </span>
    </span>
  );
}

export default function TopBar({
  sol,
  maxSol,
  connected,
  status,
  agentName,
  difficulty,
  speed,
  onPause,
  onResume,
  onNewMission,
}: TopBarProps) {
  const statusColor =
    status === 'done'
      ? colors.textDim
      : status === 'paused'
        ? colors.warning
        : colors.accent;

  const canPause = status === 'running';
  const canResume = status === 'paused';
  const isDone = status === 'done';

  return (
    <header
      className="flex items-center justify-between px-4 py-2 border-b shrink-0"
      style={{ backgroundColor: colors.surface, borderColor: colors.border }}
    >
      {/* Left: title + status */}
      <div className="flex items-center gap-4">
        <h1
          className="text-xl font-bold tracking-[0.2em]"
          style={{ color: colors.accent }}
        >
          ROVE
        </h1>
        <span
          className="text-xs uppercase tracking-widest hidden md:inline"
          style={{ color: colors.textDim }}
        >
          Mission Control
        </span>
        <span
          className="px-2 py-0.5 rounded text-xs uppercase tracking-wider mono"
          style={{ backgroundColor: `${statusColor}22`, color: statusColor }}
        >
          {status ?? 'idle'}
        </span>
      </div>

      {/* Center: SOL + agent + difficulty */}
      <div className="flex items-center gap-6 text-xs">
        <div className="text-center">
          <div className="mono text-lg" style={{ color: colors.text }}>
            {String(sol).padStart(3, '0')}
          </div>
          <div
            className="uppercase tracking-widest text-[10px]"
            style={{ color: colors.textDim }}
          >
            SOL / {maxSol}
          </div>
        </div>

        <div className="text-center hidden md:block">
          <div className="mono text-sm" style={{ color: colors.text }}>
            {agentName}
          </div>
          <div
            className="uppercase tracking-widest text-[10px]"
            style={{ color: colors.textDim }}
          >
            agent
          </div>
        </div>

        <div className="text-center hidden md:block">
          <div className="mono text-sm uppercase" style={{ color: colors.text }}>
            {difficulty}
          </div>
          <div
            className="uppercase tracking-widest text-[10px]"
            style={{ color: colors.textDim }}
          >
            difficulty
          </div>
        </div>

        <div className="text-center hidden md:block">
          <div className="mono text-sm" style={{ color: colors.text }}>
            {speed}×
          </div>
          <div
            className="uppercase tracking-widest text-[10px]"
            style={{ color: colors.textDim }}
          >
            speed
          </div>
        </div>

        <StatusDot connected={connected} />
      </div>

      {/* Right: controls */}
      <div className="flex items-center gap-2">
        <button
          onClick={onPause}
          disabled={!canPause}
          className="w-8 h-8 rounded flex items-center justify-center transition-colors disabled:opacity-30"
          style={{ backgroundColor: colors.surface2, color: colors.text }}
          title="Pause mission"
        >
          ⏸
        </button>
        <button
          onClick={onResume}
          disabled={!canResume}
          className="w-8 h-8 rounded flex items-center justify-center transition-colors disabled:opacity-30"
          style={{ backgroundColor: colors.surface2, color: colors.text }}
          title="Resume mission"
        >
          ▶
        </button>

        <button
          onClick={onNewMission}
          className="px-3 py-1.5 rounded text-xs font-medium uppercase tracking-wider transition-colors ml-2"
          style={{
            backgroundColor: isDone ? colors.success : colors.accent2,
            color: '#fff',
          }}
        >
          {isDone ? 'New Mission' : 'Abort'}
        </button>
      </div>
    </header>
  );
}