/**
 * A single terrain cell rendered as an SVG <rect>.
 * Hover shows a tooltip with the terrain name.
 */
import { TERRAIN_COLORS, TERRAIN_LABELS, TerrainType } from '../../types/mission';
import { colors } from '../../theme';

interface Props {
  x: number;
  y: number;
  size: number;
  terrain: number;
}

export default function TerrainCell({ x, y, size, terrain }: Props) {
  const type = terrain as TerrainType;
  const fill = TERRAIN_COLORS[type] ?? TERRAIN_COLORS[TerrainType.PLAIN];
  const label = TERRAIN_LABELS[type] ?? 'Unknown';

  return (
    <rect
      x={x * size}
      y={y * size}
      width={size}
      height={size}
      fill={fill}
      stroke={colors.border}
      strokeWidth={0.5}
    >
      <title>{`(${x}, ${y}) · ${label}`}</title>
    </rect>
  );
}