/**
 * Live event log for the current mission.
 * Auto-scrolls ONLY the log container, not the whole page.
 */
import { useEffect, useRef } from 'react';

import { colors, ui } from '../theme';

interface Props {
  events: string[];
}

/** Color-code events by keyword. */
function eventColor(event: string): string {
  const e = event.toLowerCase();
  if (e.includes('failure') || e.includes('fail')) return colors.danger;
  if (e.includes('success')) return colors.success;
  if (e.includes('storm') || e.includes('warning')) return colors.warning;
  if (e.includes('ai') || e.includes('decision')) return colors.accent;
  return colors.textDim;
}

export default function EventFeed({ events }: Props) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const lastCountRef = useRef(0);

  // Auto-scroll only when new events arrive — and only inside the panel.
  useEffect(() => {
    if (events.length === lastCountRef.current) return;
    lastCountRef.current = events.length;

    const el = scrollRef.current;
    if (!el) return;

    // Only auto-scroll if the user is already near the bottom.
    // This prevents fighting the user when they scroll up to read old events.
    const nearBottom =
      el.scrollHeight - el.scrollTop - el.clientHeight < 60;

    if (nearBottom) {
      el.scrollTop = el.scrollHeight;
    }
  }, [events.length]);

  return (
    <div className={`${ui.panel} flex flex-col h-full overflow-hidden`}>
      <div className="p-4 pb-2 shrink-0">
        <h2 className={ui.panelTitle}>Mission Log</h2>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 pb-4"
      >
        {events.length === 0 ? (
          <p className="text-xs" style={{ color: colors.textDim }}>
            No events yet.
          </p>
        ) : (
          <ul className="space-y-1 text-xs">
            {events.map((e, i) => (
              <li
                key={i}
                className="mono leading-relaxed"
                style={{ color: eventColor(e) }}
              >
                {e}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}