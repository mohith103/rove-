/**
 * Resource bars for the rover.
 */
import type { RoverState } from '../types/mission';
import { colors, resourceColor, ui } from '../theme';

interface Props {
  rover: RoverState | null;
}

function ResourceBar({
  label,
  value,
  max = 100,
  suffix = '%',
}: {
  label: string;
  value: number;
  max?: number;
  suffix?: string;
}) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  const color = resourceColor(pct);

  return (
    <div>
      <div className="flex justify-between items-baseline mb-1">
        <span
          className="text-xs uppercase tracking-wider"
          style={{ color: colors.textDim }}
        >
          {label}
        </span>
        <span className="mono text-xs" style={{ color: colors.text }}>
          {value.toFixed(1)}
          {suffix}
        </span>
      </div>
      <div
        className="h-1.5 rounded-full overflow-hidden"
        style={{ backgroundColor: colors.border }}
      >
        <div
          className="h-full rounded-full transition-all duration-300"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export default function ResourcePanel({ rover }: Props) {
  return (
    <div className={`${ui.panel} p-4 h-full overflow-y-auto`}>
      <h2 className={ui.panelTitle}>Rover Resources</h2>

      {!rover ? (
        <p className="text-xs" style={{ color: colors.textDim }}>
          Waiting for data…
        </p>
      ) : (
        <div className="space-y-3">
          <ResourceBar label="Energy" value={rover.energy} />
          <ResourceBar label="Oxygen" value={rover.oxygen} />
          <ResourceBar label="Water" value={rover.water} />
          <ResourceBar label="Food" value={rover.food} />
          <ResourceBar label="Battery" value={rover.battery_health} />
          <ResourceBar label="Health" value={rover.rover_health} />
          <ResourceBar label="Comms" value={rover.communication} />

          <div
            className="pt-2 mt-2 border-t grid grid-cols-2 gap-2 text-xs"
            style={{ borderColor: colors.border }}
          >
            <div>
              <div style={{ color: colors.textDim }}>Position</div>
              <div className="mono" style={{ color: colors.text }}>
                ({rover.x}, {rover.y})
              </div>
            </div>
            <div>
              <div style={{ color: colors.textDim }}>Samples</div>
              <div className="mono" style={{ color: colors.text }}>
                {rover.samples_collected} / {rover.cargo.length + 3}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}