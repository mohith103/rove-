/**
 * Tabular comparison of experiment results.
 */
import type { ExperimentRow } from '../../types/mission';
import { colors } from '../../theme';

interface Props {
  rows: ExperimentRow[];
}

export default function ResultsTable({ rows }: Props) {
  if (rows.length === 0) {
    return null;
  }

  return (
    <div
      className="rounded-lg border overflow-hidden"
      style={{ backgroundColor: colors.surface, borderColor: colors.border }}
    >
      <table className="w-full text-sm">
        <thead>
          <tr style={{ backgroundColor: colors.surface2 }}>
            <th
              className="text-left px-3 py-2 text-xs uppercase tracking-wider"
              style={{ color: colors.textDim }}
            >
              Agent
            </th>
            <th
              className="text-left px-3 py-2 text-xs uppercase tracking-wider"
              style={{ color: colors.textDim }}
            >
              Difficulty
            </th>
            <th
              className="text-right px-3 py-2 text-xs uppercase tracking-wider"
              style={{ color: colors.textDim }}
            >
              Success
            </th>
            <th
              className="text-right px-3 py-2 text-xs uppercase tracking-wider"
              style={{ color: colors.textDim }}
            >
              Samples
            </th>
            <th
              className="text-right px-3 py-2 text-xs uppercase tracking-wider"
              style={{ color: colors.textDim }}
            >
              Steps
            </th>
            <th
              className="text-right px-3 py-2 text-xs uppercase tracking-wider"
              style={{ color: colors.textDim }}
            >
              Energy
            </th>
            <th
              className="text-right px-3 py-2 text-xs uppercase tracking-wider"
              style={{ color: colors.textDim }}
            >
              Reward
            </th>
            <th
              className="text-left px-3 py-2 text-xs uppercase tracking-wider"
              style={{ color: colors.textDim }}
            >
              Top Failure
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => {
            const successColor =
              r.success_rate >= 0.5
                ? colors.success
                : r.success_rate >= 0.2
                  ? colors.warning
                  : colors.danger;
            return (
              <tr
                key={`${r.agent}-${r.difficulty}-${i}`}
                style={{
                  borderTop: `1px solid ${colors.border}`,
                }}
              >
                <td className="px-3 py-2 mono" style={{ color: colors.text }}>
                  {r.agent}
                </td>
                <td
                  className="px-3 py-2 mono"
                  style={{ color: colors.textDim }}
                >
                  {r.difficulty}
                </td>
                <td
                  className="px-3 py-2 mono text-right"
                  style={{ color: successColor }}
                >
                  {(r.success_rate * 100).toFixed(1)}%
                </td>
                <td
                  className="px-3 py-2 mono text-right"
                  style={{ color: colors.text }}
                >
                  {r.avg_samples.toFixed(2)}
                </td>
                <td
                  className="px-3 py-2 mono text-right"
                  style={{ color: colors.text }}
                >
                  {r.avg_steps.toFixed(1)}
                </td>
                <td
                  className="px-3 py-2 mono text-right"
                  style={{ color: colors.text }}
                >
                  {r.avg_energy_left.toFixed(1)}%
                </td>
                <td
                  className="px-3 py-2 mono text-right"
                  style={{ color: colors.text }}
                >
                  {r.avg_reward.toFixed(0)}
                </td>
                <td
                  className="px-3 py-2 text-xs"
                  style={{ color: colors.textDim }}
                >
                  {r.top_failure}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}