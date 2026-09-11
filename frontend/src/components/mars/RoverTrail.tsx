/**
 * Fading trail of the rover's recent path.
 * Newer positions are brighter; older ones fade out.
 */
import type { TrailPoint } from '../../types/mission';
import { colors } from '../../theme';

interface Props {
  trail: TrailPoint[];
  size: number;
}

export default function RoverTrail({ trail, size }: Props) {
  if (trail.length < 2) return null;

  const maxLen = trail.length;

  return (
    <g>
      {/* Connecting line */}
      <polyline
        points={trail
          .map((p) => `${p.x * size + size / 2},${p.y * size + size / 2}`)
          .join(' ')}
        fill="none"
        stroke={colors.accent}
        strokeWidth={size * 0.08}
        strokeOpacity={0.35}
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Fading dots — older at start, newer at end */}
      {trail.map((p, i) => {
        const ageFactor = (i + 1) / maxLen; // 0.0 → 1.0
        const r = size * 0.06 + size * 0.08 * ageFactor;
        const opacity = 0.15 + 0.5 * ageFactor;
        return (
          <circle
            key={`${p.x}-${p.y}-${i}`}
            cx={p.x * size + size / 2}
            cy={p.y * size + size / 2}
            r={r}
            fill={colors.accent}
            opacity={opacity}
          />
        );
      })}
    </g>
  );
}