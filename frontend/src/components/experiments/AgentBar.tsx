/**
 * Horizontal bar comparison for a single metric across agents.
 */
import { colors } from '../../theme';

interface Row {
  label: string;
  value: number;
  color: string;
}

interface Props {
  title: string;
  rows: Row[];
  unit?: string;
  max?: number;
}

export default function AgentBar({ title, rows, unit = '', max }: Props) {
  const maxValue = max ?? Math.max(...rows.map((r) => r.value), 1);

  return (
    <div
      className="p-4 rounded-lg border"
      style={{ backgroundColor: colors.surface, borderColor: colors.border }}
    >
      <h3
        className="text-xs uppercase tracking-widest mb-3"
        style={{ color: colors.textDim }}
      >
        {title}
      </h3>
      <div className="space-y-2">
        {rows.map((r) => {
          const pct = maxValue > 0 ? (r.value / maxValue) * 100 : 0;
          return (
            <div key={r.label}>
              <div className="flex justify-between text-xs mb-1">
                <span style={{ color: colors.text }}>{r.label}</span>
                <span className="mono" style={{ color: colors.text }}>
                  {r.value.toFixed(2)}
                  {unit}
                </span>
              </div>
              <div
                className="h-2 rounded overflow-hidden"
                style={{ backgroundColor: colors.border }}
              >
                <div
                  className="h-full rounded transition-all"
                  style={{ width: `${pct}%`, backgroundColor: r.color }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}