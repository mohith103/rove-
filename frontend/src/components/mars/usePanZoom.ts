/**
 * Lightweight pan/zoom hook for SVG views.
 *
 * Returns the current transform state plus handlers to attach to an <svg>:
 *   - wheel to zoom
 *   - mouse drag to pan
 *   - reset()
 */
import { useCallback, useRef, useState } from 'react';

interface PanZoomState {
  scale: number;
  tx: number;
  ty: number;
}

export function usePanZoom(initial = { scale: 1, tx: 0, ty: 0 }) {
  const [state, setState] = useState<PanZoomState>(initial);
  const dragging = useRef(false);
  const lastPos = useRef({ x: 0, y: 0 });

  const onWheel = useCallback((e: React.WheelEvent<SVGSVGElement>) => {
    const delta = -e.deltaY * 0.001;
    setState((s) => {
      const scale = Math.max(0.5, Math.min(8, s.scale * (1 + delta)));
      return { ...s, scale };
    });
  }, []);

  const onMouseDown = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    dragging.current = true;
    lastPos.current = { x: e.clientX, y: e.clientY };
  }, []);

  const onMouseMove = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    if (!dragging.current) return;
    const dx = e.clientX - lastPos.current.x;
    const dy = e.clientY - lastPos.current.y;
    lastPos.current = { x: e.clientX, y: e.clientY };
    setState((s) => ({ ...s, tx: s.tx + dx, ty: s.ty + dy }));
  }, []);

  const onMouseUp = useCallback(() => {
    dragging.current = false;
  }, []);

  const reset = useCallback(() => setState(initial), [initial]);

  const zoomBy = useCallback((factor: number) => {
    setState((s) => ({
      ...s,
      scale: Math.max(0.5, Math.min(8, s.scale * factor)),
    }));
  }, []);

  return {
    ...state,
    onWheel,
    onMouseDown,
    onMouseMove,
    onMouseUp,
    onMouseLeave: onMouseUp,
    reset,
    zoomBy,
  };
}