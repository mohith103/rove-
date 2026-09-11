/**
 * Panel that lets the user run a counterfactual from the current replay step.
 * Shows a comparison between the actual and counterfactual timelines.
 */
import { useState } from 'react';

import { api } from '../../services/api';
import { colors, ui } from '../../theme';
import type {
  OverrideType,
  RunCounterfactualResponse,
} from '../../types/mission';

interface Props {
  missionId: string;
  currentStep: number;
  onClose: () => void;
}

const OVERRIDES: { value: OverrideType; label: string }[] = [
  { value: 'force_return_to_base', label: 'Return to base' },
  { value: 'force_recharge', label: 'Recharge' },
  { value: 'force_repair', label: 'Repair' },
  { value: 'force_wait', label: 'Wait' },
];

export default function CounterfactualPanel({
  missionId,
  currentStep,
  onClose,
}: Props) {
  const [override, setOverride] = useState<OverrideType>('force_return_to_base');
  const [duration, setDuration] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RunCounterfactualResponse | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const response = await api.runCounterfactual(missionId, {
        fork_step: currentStep,
        override,
        override_duration: duration,
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center p-6"
      style={{ backgroundColor: 'rgba(10, 14, 20, 0.85)' }}
      onClick={onClose}
    >
      <div
        className={`${ui.panel} w-full max-w-3xl p-6 max-h-[90vh] overflow-y-auto`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2
              className="text-lg font-bold tracking-widest"
              style={{ color: colors.accent }}
            >
              WHAT IF?
            </h2>
            <p className="text-xs mt-1" style={{ color: colors.textDim }}>
              Fork from SOL {currentStep} and run an alternative future.
            </p>
          </div>
          <button
            onClick={onClose}
            className="px-3 py-1 rounded text-xs uppercase"
            style={{ backgroundColor: colors.surface2, color: colors.text }}
          >
            Close
          </button>
        </div>

        {!result && (
          <>
            <div className="space-y-4">
              <div>
                <label
                  className="text-xs uppercase tracking-widest block mb-2"
                  style={{ color: colors.textDim }}
                >
                  Override Policy
                </label>
                <div className="flex flex-wrap gap-2">
                  {OVERRIDES.map((o) => (
                    <button
                      key={o.value}
                      onClick={() => setOverride(o.value)}
                      className="px-3 py-1.5 rounded text-xs uppercase border"
                      style={{
                        backgroundColor:
                          override === o.value
                            ? `${colors.accent}22`
                            : colors.surface2,
                        borderColor:
                          override === o.value
                            ? colors.accent
                            : colors.border,
                        color:
                          override === o.value ? colors.accent : colors.text,
                      }}
                    >
                      {o.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label
                  className="text-xs uppercase tracking-widest block mb-2"
                  style={{ color: colors.textDim }}
                >
                  Duration (SOL steps)
                </label>
                <input
                  type="range"
                  min={1}
                  max={100}
                  value={duration}
                  onChange={(e) => setDuration(Number(e.target.value))}
                  className="w-full"
                />
                <div
                  className="text-right mono text-sm"
                  style={{ color: colors.text }}
                >
                  {duration} steps
                </div>
              </div>
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

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={onClose}
                className="px-4 py-2 rounded text-sm uppercase"
                style={{ backgroundColor: colors.surface2, color: colors.text }}
              >
                Cancel
              </button>
              <button
                onClick={run}
                disabled={loading}
                className="px-6 py-2 rounded text-sm uppercase tracking-widest disabled:opacity-40"
                style={{ backgroundColor: colors.accent2, color: '#fff' }}
              >
                {loading ? 'Simulating…' : 'Run Counterfactual'}
              </button>
            </div>
          </>
        )}

        {result && (
          <>
            <div
              className="p-3 rounded mb-4 text-sm"
              style={{
                backgroundColor: `${colors.accent}15`,
                border: `1px solid ${colors.accent}`,
                color: colors.text,
              }}
            >
              <strong style={{ color: colors.accent }}>Verdict:</strong>{' '}
              {result.verdict}
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <TimelineCard timeline={result.actual} />
              <TimelineCard timeline={result.counterfactual} />
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => setResult(null)}
                className="px-4 py-2 rounded text-sm uppercase"
                style={{ backgroundColor: colors.surface2, color: colors.text }}
              >
                Try Another
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 rounded text-sm uppercase"
                style={{ backgroundColor: colors.accent2, color: '#fff' }}
              >
                Done
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function TimelineCard({
  timeline,
}: {
  timeline: RunCounterfactualResponse['actual'];
}) {
  const ok = timeline.success;
  const accent = ok ? colors.success : colors.danger;

  return (
    <div
      className="p-4 rounded border"
      style={{
        backgroundColor: colors.surface2,
        borderColor: accent,
      }}
    >
      <div
        className="text-xs uppercase tracking-widest mb-1"
        style={{ color: colors.textDim }}
      >
        {timeline.label}
      </div>
      <div
        className="text-lg font-bold mb-3 mono"
        style={{ color: accent }}
      >
        {ok ? '✓ SUCCESS' : '✗ FAILED'}
      </div>
      <p className="text-xs mb-3" style={{ color: colors.textDim }}>
        {timeline.description}
      </p>
      <div className="space-y-1 text-xs">
        <Row label="SOLS" value={`${timeline.steps}`} />
        <Row label="Samples" value={`${timeline.samples_collected}`} />
        <Row label="Energy" value={`${timeline.energy_left.toFixed(1)}%`} />
        <Row label="Oxygen" value={`${timeline.oxygen_left.toFixed(1)}%`} />
        <Row label="Health" value={`${timeline.rover_health.toFixed(1)}%`} />
        {timeline.failure_reason && (
          <Row
            label="Failure"
            value={timeline.failure_reason}
            color={colors.danger}
          />
        )}
      </div>
    </div>
  );
}

function Row({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="flex justify-between">
      <span style={{ color: colors.textDim }}>{label}</span>
      <span className="mono" style={{ color: color ?? colors.text }}>
        {value}
      </span>
    </div>
  );
}