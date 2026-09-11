/**
 * Risk and confidence over time, derived from the mission's decision log.
 */
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { colors } from '../../theme';

interface Props {
  data: { step: number; risk: number; confidence: number }[];
}

export default function RiskChart({ data }: Props) {
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
        Mission Risk & AI Confidence
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="riskFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={colors.danger} stopOpacity={0.4} />
              <stop offset="95%" stopColor={colors.danger} stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="confFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={colors.success} stopOpacity={0.4} />
              <stop offset="95%" stopColor={colors.success} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={colors.border} strokeDasharray="3 3" />
          <XAxis
            dataKey="step"
            stroke={colors.textDim}
            tick={{ fontSize: 11 }}
            tickLine={false}
          />
          <YAxis
            domain={[0, 1]}
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
          <Area
            type="monotone"
            dataKey="risk"
            name="Risk"
            stroke={colors.danger}
            strokeWidth={1.5}
            fill="url(#riskFill)"
            isAnimationActive={false}
          />
          <Area
            type="monotone"
            dataKey="confidence"
            name="Confidence"
            stroke={colors.success}
            strokeWidth={1.5}
            fill="url(#confFill)"
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}