/**
 * Mission Replay with counterfactual analysis.
 */
import { useEffect, useMemo, useState } from 'react';

import MarsMap from '../components/MarsMap';
import EventFeed from '../components/EventFeed';
import CommanderPanel from '../components/CommanderPanel';
import ResourcePanel from '../components/ResourcePanel';
import CounterfactualPanel from '../components/counterfactual/CounterfactualPanel';
import { api } from '../services/api';
import { colors, ui } from '../theme';
import type { ReplayPayload, WorldState } from '../types/mission';

interface Props {
  missionId: string;
  onExit: () => void;
}

const SPEEDS = [0.5, 1, 2, 4, 8];

export default function ReplayPage({ missionId, onExit }: Props) {
  const [payload, setPayload] = useState<ReplayPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [frameIndex, setFrameIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(2);
  const [showCF, setShowCF] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await api.getReplay(missionId);
        if (!cancelled) {
          setPayload(data);
          setFrameIndex(0);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [missionId]);

  useEffect(() => {
    if (!playing || !payload) return;
    const total = payload.frames.length;
    if (total === 0) return;

    const interval = setInterval(() => {
      setFrameIndex((i) => {
        const next = i + 1;
        if (next >= total) {
          setPlaying(false);
          return total - 1;
        }
        return next;
      });
    }, 1000 / speed);

    return () => clearInterval(interval);
  }, [playing, speed, payload]);

  const worldState = useMemo<WorldState | null>(() => {
    if (!payload || payload.frames.length === 0) return null;
    const frame = payload.frames[frameIndex];
    if (!frame) return null;
    return {
      step: frame.step,
      max_steps: payload.max_steps,
      rover: frame.rover,
      base: frame.base,
      science_sites: frame.science_sites,
      done: frame.done,
      success: frame.success,
      failure_reason: frame.failure_reason,
      events: payload.events.slice(0, frame.step + 1),
      terrain: payload.terrain,
      width: payload.width,
      height: payload.height,
    };
  }, [payload, frameIndex]);

  const currentDecision = payload?.decisions[frameIndex] ?? null;

  const visibleEvents = useMemo(() => {
    if (!payload) return [];
    return payload.events.filter((e) => {
      const match = e.match(/\[SOL (\d+)\]/);
      if (!match) return true;
      return parseInt(match[1], 10) <= frameIndex;
    });
  }, [payload, frameIndex]);

  if (error) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ backgroundColor: colors.bg }}
      >
        <div className={`${ui.panel} p-6 max-w-lg`}>
          <h1
            className="text-xl font-bold mb-2"
            style={{ color: colors.danger }}
          >
            Failed to load replay
          </h1>
          <p className="text-sm" style={{ color: colors.textDim }}>
            {error}
          </p>
          <button
            onClick={onExit}
            className="mt-4 px-4 py-2 rounded text-sm"
            style={{ backgroundColor: colors.accent2, color: '#fff' }}
          >
            Back
          </button>
        </div>
      </div>
    );
  }

  if (!payload) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ backgroundColor: colors.bg }}
      >
        <p
          className="text-xs uppercase tracking-widest"
          style={{ color: colors.textDim }}
        >
          Loading replay…
        </p>
      </div>
    );
  }

  const totalFrames = payload.frames.length;
  const progress = totalFrames > 1 ? frameIndex / (totalFrames - 1) : 0;

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{ backgroundColor: colors.bg }}
    >
      <header
        className="flex items-center justify-between px-4 py-2 border-b shrink-0"
        style={{ backgroundColor: colors.surface, borderColor: colors.border }}
      >
        <div className="flex items-center gap-4">
          <h1
            className="text-xl font-bold tracking-[0.2em]"
            style={{ color: colors.accent }}
          >
            ROVE
          </h1>
          <span
            className="text-xs uppercase tracking-widest"
            style={{ color: colors.textDim }}
          >
            Mission Replay
          </span>
          <span
            className="px-2 py-0.5 rounded text-xs uppercase tracking-wider mono"
            style={{
              backgroundColor: payload.success
                ? `${colors.success}22`
                : `${colors.danger}22`,
              color: payload.success ? colors.success : colors.danger,
            }}
          >
            {payload.success ? 'SUCCESS' : 'FAILED'}
          </span>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <span className="mono" style={{ color: colors.text }}>
            {payload.agent}
          </span>
          <span style={{ color: colors.textDim }}>·</span>
          <span className="mono" style={{ color: colors.text }}>
            {payload.difficulty}
          </span>
          <span style={{ color: colors.textDim }}>·</span>
          <span className="mono" style={{ color: colors.text }}>
            seed {payload.seed}
          </span>
          <button
            onClick={onExit}
            className="ml-4 px-3 py-1.5 rounded text-xs uppercase tracking-wider"
            style={{ backgroundColor: colors.surface2, color: colors.text }}
          >
            Exit
          </button>
        </div>
      </header>

      <div
        className="flex items-center gap-4 px-4 py-3 border-b shrink-0"
        style={{ backgroundColor: colors.surface, borderColor: colors.border }}
      >
        <button
          onClick={() => setPlaying((p) => !p)}
          className="w-10 h-10 rounded flex items-center justify-center text-lg"
          style={{ backgroundColor: colors.accent2, color: '#fff' }}
        >
          {playing ? '⏸' : '▶'}
        </button>

        <button
          onClick={() => setFrameIndex(0)}
          className="px-3 py-2 rounded text-xs uppercase"
          style={{ backgroundColor: colors.surface2, color: colors.text }}
        >
          ⏮ Start
        </button>

        <input
          type="range"
          min={0}
          max={Math.max(0, totalFrames - 1)}
          value={frameIndex}
          onChange={(e) => setFrameIndex(Number(e.target.value))}
          className="flex-1"
        />

        <span
          className="mono text-sm w-24 text-right"
          style={{ color: colors.text }}
        >
          SOL {String(frameIndex).padStart(3, '0')}
        </span>
        <span
          className="mono text-xs w-16 text-right"
          style={{ color: colors.textDim }}
        >
          {(progress * 100).toFixed(0)}%
        </span>

        <select
          value={speed}
          onChange={(e) => setSpeed(Number(e.target.value))}
          className="px-2 py-1 rounded text-xs"
          style={{ backgroundColor: colors.surface2, color: colors.text }}
        >
          {SPEEDS.map((s) => (
            <option key={s} value={s}>
              {s}×
            </option>
          ))}
        </select>

        <button
          onClick={() => setShowCF(true)}
          className="px-3 py-2 rounded text-xs uppercase tracking-wider"
          style={{ backgroundColor: colors.warning, color: '#000' }}
        >
          Ask: What if?
        </button>
      </div>

      <main className="flex-1 grid gap-4 p-4 grid-cols-1 lg:grid-cols-3 min-h-0">
        <div className="lg:col-span-2 h-[560px]">
          <MarsMap state={worldState} />
        </div>

        <div className="flex flex-col gap-4 h-[560px]">
          <div className="flex-1 min-h-0">
            <CommanderPanel decision={currentDecision} />
          </div>
          <div className="flex-1 min-h-0">
            <ResourcePanel rover={worldState?.rover ?? null} />
          </div>
        </div>

        <div className="lg:col-span-3 h-[220px]">
          <EventFeed events={visibleEvents} />
        </div>
      </main>

      {showCF && (
        <CounterfactualPanel
          missionId={missionId}
          currentStep={frameIndex}
          onClose={() => setShowCF(false)}
        />
      )}
    </div>
  );
}