/**
 * The main Mars grid SVG. Renders terrain cells, science sites, base,
 * rover, hover outline, and the rover's trail.
 */
import type { HoverCell, TrailPoint, WorldState } from '../../types/mission';
import TerrainCell from './TerrainCell';
import ScienceMarker from './ScienceMarker';
import RoverMarker from './RoverMarker';
import RoverTrail from './RoverTrail';
import { colors } from '../../theme';

interface Props {
  state: WorldState;
  cellSize: number;
  hoveredCell?: HoverCell | null;
  trail?: TrailPoint[];
}

export default function MarsGrid({
  state,
  cellSize,
  hoveredCell = null,
  trail = [],
}: Props) {
  const { terrain, width, height, science_sites, base, rover } = state;

  return (
    <g>
      {/* Terrain layer */}
      {terrain.map((row, y) =>
        row.map((cell, x) => (
          <TerrainCell
            key={`${x}-${y}`}
            x={x}
            y={y}
            size={cellSize}
            terrain={cell}
          />
        )),
      )}

      {/* Rover trail (under markers, above terrain) */}
      <RoverTrail trail={trail} size={cellSize} />

      {/* Base marker */}
      <g>
        <rect
          x={base.x * cellSize + cellSize * 0.15}
          y={base.y * cellSize + cellSize * 0.15}
          width={cellSize * 0.7}
          height={cellSize * 0.7}
          fill="#0a0e14"
          stroke="#4db8ff"
          strokeWidth={1.2}
        >
          <title>Base Station</title>
        </rect>
      </g>

      {/* Science sites */}
      {science_sites.map((s, i) => (
        <ScienceMarker key={i} site={s} size={cellSize} />
      ))}

      {/* Rover (top layer, above trail) */}
      <RoverMarker rover={rover} size={cellSize} />

      {/* Hover outline */}
      {hoveredCell && hoveredCell.x < width && hoveredCell.y < height && (
        <rect
          x={hoveredCell.x * cellSize}
          y={hoveredCell.y * cellSize}
          width={cellSize}
          height={cellSize}
          fill="none"
          stroke={colors.accent}
          strokeWidth={1.5}
          pointerEvents="none"
        />
      )}

      {/* Bounding frame */}
      <rect
        x={0}
        y={0}
        width={width * cellSize}
        height={height * cellSize}
        fill="none"
        stroke="transparent"
      />
    </g>
  );
}