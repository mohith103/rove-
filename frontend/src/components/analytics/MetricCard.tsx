/**
 * A compact stat card for the analytics dashboard.
 */
import { colors } from '../../theme';

interface Props {
  label: string;
  value: string | number;
  hint?: string;
  color?: string;
}

export default function MetricCard({ label, value, hint, color }: Props) {
  return (
    <div
      className="p-4 rounded-lg border"
      style={{
        backgroundColor: colors.surface,
        borderColor: colors.border,
      }}
    >
      <div
        className="text-xs uppercase tracking-widest mb-2"
        style={{ color: colors.textDim }}
      >
        {label}
      </div>
      <div
        className="mono text-2xl font-semibold"
        style={{ color: color ?? colors.text }}
      >
        {value}
      </div>
      {hint && (
        <div className="text-xs mt-1" style={{ color: colors.textMuted }}>
          {hint}
        </div>
      )}
    </div>
  );
}