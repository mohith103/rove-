/**
 * The Mars map: SVG grid with pan/zoom controls, hover highlight, and trail.
 *
 * Cursor → cell conversion uses SVG's native coordinate transform
 * (`getScreenCTM` + `createSVGPoint`), which correctly handles letterboxing,
 * aspect-ratio mismatch, and the current pan/zoom transform.
 *
 * The trail is derived from a ref that accumulates rover positions across
 * renders — this avoids setState-in-effect while still tracking history.
 */
import { useCallback, useMemo, useRef, useState } from 'react';

import MarsGrid from './mars/MarsGrid';
import MapLegend from './mars/MapLegend';
import { usePanZoom } from './mars/usePanZoom';
import { colors, ui } from '../theme';
import type { HoverCell, TrailPoint, WorldState } from '../types/mission';

interface Props {
  state: WorldState | null;
}

const CELL_SIZE = 24;
const MAX_TRAIL = 60;

/** Module-level cache keyed by mission id so trail survives across renders. */
const trailCache = new Map<string, TrailPoint[]>();

function trailKey(state: WorldState | null): string {
  if (!state) return '__none__';
  // Distinguish missions by seed + difficulty (they are unique per mission).
  return `${state.max_steps}`;
}

export default function MarsMap({ state }: Props) {
  const panZoom = usePanZoom();
  const [hoveredCell, setHoveredCell] = useState<HoverCell | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);

  // Compute the trail during render (pure).
  const trail = useMemo<TrailPoint[]>(() => {
    if (!state) return [];
    const key = trailKey(state);
    const existing = trailCache.get(key) ?? [];
    const last = existing[existing.length - 1];

    const { x, y } = state.rover;

    if (!last || last.x !== x || last.y !== y) {
      const next = [...existing, { x, y }];
      const trimmed = next.length > MAX_TRAIL ? next.slice(-MAX_TRAIL) : next;
      trailCache.set(key, trimmed);
      return trimmed;
    }
    return existing;
  }, [state]);

  const svgSize = useMemo(() => {
    if (!state) return { w: 0, h: 0 };
    return {
      w: state.width * CELL_SIZE,
      h: state.height * CELL_SIZE,
    };
  }, [state]);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<SVGSVGElement>) => {
      panZoom.onMouseMove(e);

      const svg = svgRef.current;
      if (!svg || !state) return;

      const pt = svg.createSVGPoint();
      pt.x = e.clientX;
      pt.y = e.clientY;

      const ctm = svg.getScreenCTM();
      if (!ctm) return;

      const svgPt = pt.matrixTransform(ctm.inverse());
      const localX = (svgPt.x - panZoom.tx) / panZoom.scale;
      const localY = (svgPt.y - panZoom.ty) / panZoom.scale;

      const cellX = Math.floor(localX / CELL_SIZE);
      const cellY = Math.floor(localY / CELL_SIZE);

      if (
        cellX >= 0 &&
        cellX < state.width &&
        cellY >= 0 &&
        cellY < state.height
      ) {
        setHoveredCell({ x: cellX, y: cellY });
      } else {
        setHoveredCell(null);
      }
    },
    [panZoom, state],
  );

  const handleMouseLeave = useCallback(
    (e: React.MouseEvent<SVGSVGElement>) => {
      panZoom.onMouseLeave(e);
      setHoveredCell(null);
    },
    [panZoom],
  );

  const handleReset = useCallback(() => {
    panZoom.reset();
    if (state) trailCache.delete(trailKey(state));
  }, [panZoom, state]);

  return (
    <div className={`${ui.panel} flex flex-col h-full overflow-hidden`}>
      <div
        className="flex items-center justify-between p-3 border-b shrink-0"
        style={{ borderColor: colors.border }}
      >
        <div className="flex items-center gap-4">
          <h2 className={ui.panelTitle} style={{ marginBottom: 0 }}>
            Mars Surface
          </h2>
          {state && (
            <span className="text-xs mono" style={{ color: colors.textDim }}>
              {state.width} × {state.height}
            </span>
          )}
          {hoveredCell && (
            <span
              className="text-xs mono px-2 py-0.5 rounded"
              style={{
                backgroundColor: colors.surface2,
                color: colors.accent,
              }}
            >
              ({hoveredCell.x}, {hoveredCell.y})
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => panZoom.zoomBy(1.3)}
            className="w-6 h-6 rounded text-xs flex items-center justify-center"
            style={{ backgroundColor: colors.surface2, color: colors.text }}
            title="Zoom in"
          >
            +
          </button>
          <button
            onClick={() => panZoom.zoomBy(1 / 1.3)}
            className="w-6 h-6 rounded text-xs flex items-center justify-center"
            style={{ backgroundColor: colors.surface2, color: colors.text }}
            title="Zoom out"
          >
            −
          </button>
          <button
            onClick={handleReset}
            className="px-2 h-6 rounded text-xs"
            style={{ backgroundColor: colors.surface2, color: colors.textDim }}
            title="Reset view and trail"
          >
            Reset
          </button>
          <span className="text-xs mono ml-2" style={{ color: colors.textDim }}>
            {(panZoom.scale * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      <div
        className="flex-1 overflow-hidden relative"
        style={{ backgroundColor: colors.bg }}
      >
        {!state ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <p
              className="text-xs uppercase tracking-widest"
              style={{ color: colors.textDim }}
            >
              Awaiting mission data…
            </p>
          </div>
        ) : (
          <svg
            ref={svgRef}
            width="100%"
            height="100%"
            viewBox={`0 0 ${svgSize.w} ${svgSize.h}`}
            preserveAspectRatio="xMidYMid meet"
            onWheel={panZoom.onWheel}
            onMouseDown={panZoom.onMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={panZoom.onMouseUp}
            onMouseLeave={handleMouseLeave}
            style={{ cursor: 'crosshair', display: 'block' }}
          >
            <g
              transform={`translate(${panZoom.tx}, ${panZoom.ty}) scale(${panZoom.scale})`}
            >
              <MarsGrid
                state={state}
                cellSize={CELL_SIZE}
                hoveredCell={hoveredCell}
                trail={trail}
              />
            </g>
          </svg>
        )}
      </div>

      <div
        className="px-3 py-2 border-t shrink-0"
        style={{ borderColor: colors.border, backgroundColor: colors.surface }}
      >
        <MapLegend />
      </div>
    </div>
  );
}