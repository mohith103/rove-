/**
 * Multi-line chart for resource levels over time.
 * Each series is one resource (energy, oxygen, water, etc.).
 */
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { colors } from '../../theme';

export interface ResourceSeries {
  key: string;
  label: string;
  color: string;
}

interface Props {
  data: Record<string, number | string>[];
  series: ResourceSeries[];
  yMax?: number;
  title?: string;
}

export default function ResourceChart({
  data,
  series,
  yMax = 100,
  title,
}: Props) {
  return (
    <div
      className="p-4 rounded-lg border"
      style={{
        backgroundColor: colors.surface,
        borderColor: colors.border,
      }}
    >
      {title && (
        <h3
          className="text-xs uppercase tracking-widest mb-3"
          style={{ color: colors.textDim }}
        >
          {title}
        </h3>
      )}
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid stroke={colors.border} strokeDasharray="3 3" />
          <XAxis
            dataKey="step"
            stroke={colors.textDim}
            tick={{ fontSize: 11 }}
            tickLine={false}
          />
          <YAxis
            domain={[0, yMax]}
            stroke={colors.textDim}
            tick={{ fontSize: 11 }}
            tickLine={false}
            width={36}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: colors.surface2,
              border: `1px solid ${colors.border}`,
              borderRadius: 6,
              fontSize: 12,
            }}
            labelStyle={{ color: colors.text }}
          />
          <Legend
            wrapperStyle={{ fontSize: 11, color: colors.textDim }}
            iconType="line"
          />
          {series.map((s) => (
            <Line
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.label}
              stroke={s.color}
              strokeWidth={1.5}
              dot={false}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}