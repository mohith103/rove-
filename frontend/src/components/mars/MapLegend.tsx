/**
 * Terrain color legend for the Mars map.
 */
import { TERRAIN_COLORS, TERRAIN_LABELS, TerrainType } from '../../types/mission';
import { colors } from '../../theme';

const LEGEND_ITEMS: TerrainType[] = [
  TerrainType.PLAIN,
  TerrainType.ROCK,
  TerrainType.CRATER,
  TerrainType.MOUNTAIN,
  TerrainType.SAND,
  TerrainType.BASE,
  TerrainType.SCIENCE_SITE,
];

export default function MapLegend() {
  return (
    <div className="flex flex-wrap items-center gap-3 text-xs">
      {LEGEND_ITEMS.map((t) => (
        <div key={t} className="flex items-center gap-1.5">
          <span
            className="w-3 h-3 rounded-sm border"
            style={{
              backgroundColor: TERRAIN_COLORS[t],
              borderColor: colors.border,
            }}
          />
          <span style={{ color: colors.textDim }}>{TERRAIN_LABELS[t]}</span>
        </div>
      ))}
    </div>
  );
}