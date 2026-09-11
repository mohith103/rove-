/**
 * React hook that streams live updates for a mission.
 *
 * Maintains a growing event log client-side so nothing is lost when the
 * backend's rolling buffer rolls over. On first connect, backfills from
 * the REST endpoint.
 */
import { useEffect, useRef, useState } from 'react';

import { MissionSocket } from '../services/websocket';
import { api, missionStreamUrl } from '../services/api';
import type { Decision, MissionStatus, WorldState } from '../types/mission';

interface StreamState {
  state: WorldState | null;
  decision: Decision | null;
  status: MissionStatus | null;
  connected: boolean;
  error: string | null;
  events: string[];
}

const MAX_EVENTS = 5000;

export function useMissionStream(missionId: string | null): StreamState {
  const [state, setState] = useState<WorldState | null>(null);
  const [decision, setDecision] = useState<Decision | null>(null);
  const [status, setStatus] = useState<MissionStatus | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [events, setEvents] = useState<string[]>([]);

  // Ref mirrors of mutable state, for use inside WebSocket callbacks.
  const seenEventsRef = useRef<Set<string>>(new Set());
  const eventsRef = useRef<string[]>([]);

  useEffect(() => {
    if (!missionId) return;

    // Reset local state for the new mission — done via setters, not
    // direct assignment, and only when a mission id exists.
    seenEventsRef.current = new Set();
    eventsRef.current = [];
    // Note: state, decision, status, events are intentionally not reset
    // here. They are replaced by the first REST + WS responses.

    let cancelled = false;

    // 1) Backfill via REST.
    (async () => {
      try {
        const detail = await api.getMission(missionId);
        if (cancelled) return;
        const fullEvents = detail.events ?? [];
        eventsRef.current = fullEvents;
        seenEventsRef.current = new Set(fullEvents);
        setEvents(fullEvents);
        if (detail.state) setState(detail.state);
        if (detail.decision) setDecision(detail.decision);
        setStatus(detail.status);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      }
    })();

    // 2) WebSocket live stream.
    const socket = new MissionSocket(missionStreamUrl(missionId));

    const offMessage = socket.onMessage((payload) => {
      setConnected(true);
      if (payload.error) {
        setError(payload.error);
        return;
      }
      if (payload.state) {
        setState(payload.state);

        const incoming = payload.state.events ?? [];
        const newOnes: string[] = [];
        for (const e of incoming) {
          if (!seenEventsRef.current.has(e)) {
            seenEventsRef.current.add(e);
            newOnes.push(e);
          }
        }
        if (newOnes.length > 0) {
          const merged = [...eventsRef.current, ...newOnes];
          const trimmed =
            merged.length > MAX_EVENTS ? merged.slice(-MAX_EVENTS) : merged;
          eventsRef.current = trimmed;
          setEvents(trimmed);
        }
      }
      if (payload.last_decision !== undefined) setDecision(payload.last_decision);
      if (payload.summary) setStatus(payload.summary.status);
      if (payload.status === 'done') setStatus('done');
      setError(null);
    });

    socket.onError(() => {
      setError('WebSocket error');
      setConnected(false);
    });

    socket.onClose(() => {
      setConnected(false);
    });

    socket.connect();

    return () => {
      cancelled = true;
      offMessage();
      socket.close();
    };
  }, [missionId]);

  return { state, decision, status, connected, error, events };
}