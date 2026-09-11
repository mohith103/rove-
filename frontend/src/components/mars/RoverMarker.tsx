/**
 * The rover marker with a pulsing halo and hover info.
 */
import type { RoverState } from '../../types/mission';
import { colors } from '../../theme';

interface Props {
  rover: RoverState;
  size: number;
}

export default function RoverMarker({ rover, size }: Props) {
  const cx = rover.x * size + size / 2;
  const cy = rover.y * size + size / 2;
  const r = size * 0.32;

  return (
    <g>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={colors.accent} strokeWidth={0.5}>
        <animate
          attributeName="r"
          values={`${r};${r * 1.8}`}
          dur="1.5s"
          repeatCount="indefinite"
        />
        <animate
          attributeName="opacity"
          values="0.9;0"
          dur="1.5s"
          repeatCount="indefinite"
        />
      </circle>

      <circle
        cx={cx}
        cy={cy}
        r={r}
        fill={colors.accent}
        stroke="#fff"
        strokeWidth={0.8}
      >
        <title>
          {`Rover (${rover.x}, ${rover.y}) · E ${rover.energy.toFixed(0)}% · O2 ${rover.oxygen.toFixed(0)}%`}
        </title>
      </circle>

      <circle cx={cx} cy={cy} r={r * 0.3} fill="#0a0e14" />
    </g>
  );
}