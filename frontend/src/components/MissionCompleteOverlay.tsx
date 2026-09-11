/**
 * Full-screen overlay shown when a mission ends.
 * Offers to close, replay, view analytics, or start a new mission.
 */
import { colors, ui } from '../theme';
import type { MissionStatus, WorldState } from '../types/mission';

interface Props {
  state: WorldState;
  status: MissionStatus;
  onClose: () => void;
  onNewMission: () => void;
  onReplay: () => void;
  onAnalytics: () => void;
}

function StatRow({
  label,
  value,
  color,
}: {
  label: string;
  value: string | number;
  color?: string;
}) {
  return (
    <div
      className="flex justify-between items-baseline py-1.5 border-b"
      style={{ borderColor: colors.border }}
    >
      <span
        className="text-xs uppercase tracking-wider"
        style={{ color: colors.textDim }}
      >
        {label}
      </span>
      <span className="mono text-sm" style={{ color: color ?? colors.text }}>
        {value}
      </span>
    </div>
  );
}

export default function MissionCompleteOverlay({
  state,
  onClose,
  onNewMission,
  onReplay,
  onAnalytics,
}: Props) {
  const success = state.success;
  const accentColor = success ? colors.success : colors.danger;
  const title = success ? 'MISSION COMPLETE' : 'MISSION FAILED';
  const badge = success ? '✓ SUCCESS' : '✗ FAILED';

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-6"
      style={{ backgroundColor: 'rgba(10, 14, 20, 0.85)' }}
      onClick={onClose}
    >
      <div
        className={`${ui.panel} w-full max-w-lg p-6 relative`}
        style={{ borderColor: accentColor }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Title */}
        <div className="mb-6">
          <div
            className="text-xs uppercase tracking-[0.3em] mb-2"
            style={{ color: colors.textDim }}
          >
            {title}
          </div>
          <div
            className="text-3xl font-bold tracking-widest"
            style={{ color: accentColor }}
          >
            {badge}
          </div>
        </div>

        {/* Stats */}
        <div className="space-y-0 mb-6">
          <StatRow
            label="SOLS Elapsed"
            value={`${state.step} / ${state.max_steps}`}
          />
          <StatRow
            label="Samples Collected"
            value={state.rover.samples_collected}
            color={success ? colors.success : colors.text}
          />
          <StatRow
            label="Energy Remaining"
            value={`${state.rover.energy.toFixed(1)}%`}
            color={state.rover.energy < 20 ? colors.danger : colors.text}
          />
          <StatRow
            label="Rover Health"
            value={`${state.rover.rover_health.toFixed(1)}%`}
            color={state.rover.rover_health < 40 ? colors.warning : colors.text}
          />
          <StatRow
            label="Failure Reason"
            value={state.failure_reason ?? '—'}
            color={state.failure_reason ? colors.danger : colors.textDim}
          />
        </div>

        {/* Actions — 2 rows */}
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={onClose}
            className="py-2 rounded text-sm font-medium uppercase tracking-wider"
            style={{ backgroundColor: colors.surface2, color: colors.text }}
          >
            Close
          </button>
          <button
            onClick={onReplay}
            className="py-2 rounded text-sm font-medium uppercase tracking-wider"
            style={{ backgroundColor: colors.warning, color: '#000' }}
          >
            Replay
          </button>
          <button
            onClick={onAnalytics}
            className="col-span-2 py-2 rounded text-sm font-medium uppercase tracking-wider"
            style={{ backgroundColor: colors.accent, color: '#000' }}
          >
            View Analytics
          </button>
          <button
            onClick={onNewMission}
            className="col-span-2 py-2 rounded text-sm font-medium uppercase tracking-wider"
            style={{ backgroundColor: colors.accent2, color: '#fff' }}
          >
            New Mission
          </button>
        </div>

        <p
          className="text-xs mt-4 text-center"
          style={{ color: colors.textMuted }}
        >
          Click outside to dismiss.
        </p>
      </div>
    </div>
  );
}