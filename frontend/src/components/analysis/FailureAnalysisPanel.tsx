/**
 * Shows automatic failure analysis for a completed mission.
 */
import { useEffect, useState } from 'react';

import { api } from '../../services/api';
import { colors } from '../../theme';
import type { AnalysisResponse, CriticalMoment } from '../../types/mission';

interface Props {
  missionId: string;
}

function SeverityDot({ severity }: { severity: CriticalMoment['severity'] }) {
  const color =
    severity === 'critical'
      ? colors.danger
      : severity === 'warning'
        ? colors.warning
        : colors.accent;
  return (
    <span
      className="inline-block w-2 h-2 rounded-full mt-1.5 shrink-0"
      style={{ backgroundColor: color }}
    />
  );
}

export default function FailureAnalysisPanel({ missionId }: Props) {
  const [data, setData] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const result = await api.getFailureAnalysis(missionId);
        if (!cancelled) setData(result);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [missionId]);

  if (error) {
    return (
      <div
        className="p-4 rounded-lg border"
        style={{
          backgroundColor: colors.surface,
          borderColor: colors.border,
        }}
      >
        <p className="text-sm" style={{ color: colors.textDim }}>
          Failure analysis unavailable: {error}
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <div
        className="p-4 rounded-lg border"
        style={{
          backgroundColor: colors.surface,
          borderColor: colors.border,
        }}
      >
        <p
          className="text-xs uppercase tracking-widest"
          style={{ color: colors.textDim }}
        >
          Loading failure analysis…
        </p>
      </div>
    );
  }

  const accent = data.success ? colors.success : colors.danger;

  return (
    <div
      className="p-4 rounded-lg border"
      style={{
        backgroundColor: colors.surface,
        borderColor: colors.border,
      }}
    >
      <h3
        className="text-xs uppercase tracking-widest mb-3"
        style={{ color: colors.textDim }}
      >
        Failure Analysis
      </h3>

      <div
        className="p-3 rounded mb-4 text-sm"
        style={{
          backgroundColor: `${accent}15`,
          border: `1px solid ${accent}`,
          color: colors.text,
        }}
      >
        <strong style={{ color: accent }}>
          {data.success ? 'Result:' : 'Primary cause:'}
        </strong>{' '}
        {data.primary_cause}
        <div className="text-xs mt-2" style={{ color: colors.textDim }}>
          {data.summary}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data.contributing_factors.length > 0 && (
          <div>
            <h4
              className="text-xs uppercase tracking-widest mb-2"
              style={{ color: colors.textDim }}
            >
              Contributing Factors
            </h4>
            <ul className="space-y-1 text-sm">
              {data.contributing_factors.map((f, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2"
                  style={{ color: colors.text }}
                >
                  <span
                    className="inline-block w-1.5 h-1.5 rounded-full mt-2 shrink-0"
                    style={{ backgroundColor: colors.warning }}
                  />
                  <span>{f}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {data.recommendations.length > 0 && (
          <div>
            <h4
              className="text-xs uppercase tracking-widest mb-2"
              style={{ color: colors.textDim }}
            >
              Recommendations
            </h4>
            <ul className="space-y-1 text-sm">
              {data.recommendations.map((r, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2"
                  style={{ color: colors.text }}
                >
                  <span
                    className="inline-block w-1.5 h-1.5 rounded-full mt-2 shrink-0"
                    style={{ backgroundColor: colors.accent }}
                  />
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {data.critical_moments.length > 0 && (
        <div
          className="mt-4 pt-4 border-t"
          style={{ borderColor: colors.border }}
        >
          <h4
            className="text-xs uppercase tracking-widest mb-2"
            style={{ color: colors.textDim }}
          >
            Critical Moments
          </h4>
          <div className="space-y-1.5">
            {data.critical_moments.map((m, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <SeverityDot severity={m.severity} />
                <span
                  className="mono text-xs shrink-0 w-16"
                  style={{ color: colors.textDim }}
                >
                  SOL {String(m.step).padStart(3, '0')}
                </span>
                <span style={{ color: colors.text }}>{m.detail}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
