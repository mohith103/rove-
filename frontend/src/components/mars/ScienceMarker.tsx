/**
 * Diamond marker for a science site.
 * Collected sites fade out; uncollected sites pulse.
 */
import type { ScienceSite } from '../../types/mission';
import { colors } from '../../theme';

interface Props {
  site: ScienceSite;
  size: number;
}

export default function ScienceMarker({ site, size }: Props) {
  const cx = site.x * size + size / 2;
  const cy = site.y * size + size / 2;
  const r = size * 0.28;

  const fill = site.collected ? colors.textMuted : colors.warning;
  const stroke = site.collected ? colors.textMuted : '#fff';
  const opacity = site.collected ? 0.4 : 1.0;

  return (
    <g opacity={opacity}>
      {!site.collected && (
        <circle cx={cx} cy={cy} r={r * 1.8} fill="none" stroke={fill} strokeWidth={0.4}>
          <animate
            attributeName="r"
            values={`${r * 1.4};${r * 2.2};${r * 1.4}`}
            dur="2.5s"
            repeatCount="indefinite"
          />
          <animate
            attributeName="opacity"
            values="0.6;0.1;0.6"
            dur="2.5s"
            repeatCount="indefinite"
          />
        </circle>
      )}

      <polygon
        points={`${cx},${cy - r} ${cx + r},${cy} ${cx},${cy + r} ${cx - r},${cy}`}
        fill={fill}
        stroke={stroke}
        strokeWidth={0.8}
      >
        <title>
          {`${site.sample_type} · value ${site.value} · ${site.collected ? 'collected' : 'available'}`}
        </title>
      </polygon>
    </g>
  );
}