/**
 * Analytics screen for a completed mission.
 */
import { useEffect, useMemo, useState } from 'react';

import MetricCard from '../components/analytics/MetricCard';
import ResourceChart from '../components/analytics/ResourceChart';
import RiskChart from '../components/analytics/RiskChart';
import FailureAnalysisPanel from '../components/analysis/FailureAnalysisPanel';
import { api } from '../services/api';
import { colors, ui } from '../theme';
import type { ReplayPayload } from '../types/mission';

interface Props {
  missionId: string;
  onExit: () => void;
}

interface Row {
  step: number;
  energy: number;
  oxygen: number;
  water: number;
  food: number;
  battery: number;
  health: number;
  risk: number;
  confidence: number;
}

export default function AnalyticsPage({ missionId, onExit }: Props) {
  const [payload, setPayload] = useState<ReplayPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await api.getReplay(missionId);
        if (!cancelled) setPayload(data);
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

  const data = useMemo<Row[]>(() => {
    if (!payload) return [];
    return payload.frames.map((frame, i) => {
      const decision = payload.decisions[i];
      return {
        step: frame.step,
        energy: frame.rover.energy,
        oxygen: frame.rover.oxygen,
        water: frame.rover.water,
        food: frame.rover.food,
        battery: frame.rover.battery_health,
        health: frame.rover.rover_health,
        risk: decision?.explanation.risk_estimate ?? 0,
        confidence: decision?.explanation.confidence ?? 0,
      };
    });
  }, [payload]);

  const metrics = useMemo(() => {
    if (!payload || payload.frames.length === 0) return null;
    const frames = payload.frames;
    const last = frames[frames.length - 1];

    let distance = 0;
    for (let i = 1; i < frames.length; i++) {
      distance +=
        Math.abs(frames[i].rover.x - frames[i - 1].rover.x) +
        Math.abs(frames[i].rover.y - frames[i - 1].rover.y);
    }

    const avgEnergy =
      frames.reduce((s, f) => s + f.rover.energy, 0) / frames.length;
    const avgOxygen =
      frames.reduce((s, f) => s + f.rover.oxygen, 0) / frames.length;

    const criticalEnergySteps = frames.filter((f) => f.rover.energy < 20).length;
    const criticalOxygenSteps = frames.filter((f) => f.rover.oxygen < 25).length;

    const failures = payload.events.filter((e) => e.includes('FAILURE:')).length;

    const peakRisk = payload.decisions.reduce((max, d) => {
      if (!d) return max;
      return Math.max(max, d.explanation.risk_estimate);
    }, 0);

    const samplesCollected = last.rover.samples_collected;
    const survivalFraction = (last.rover.energy + last.rover.oxygen) / 200;
    const score = Math.round(
      samplesCollected * 100 + survivalFraction * 200 - failures * 20,
    );

    return {
      distance,
      avgEnergy,
      avgOxygen,
      criticalEnergySteps,
      criticalOxygenSteps,
      failures,
      peakRisk,
      samplesCollected,
      duration: last.step,
      score,
      success: payload.success,
    };
  }, [payload]);

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
            Failed to load analytics
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

  if (!payload || !metrics) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ backgroundColor: colors.bg }}
      >
        <p
          className="text-xs uppercase tracking-widest"
          style={{ color: colors.textDim }}
        >
          Loading analytics…
        </p>
      </div>
    );
  }

  const successColor = payload.success ? colors.success : colors.danger;

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
            Mission Analytics
          </span>
          <span
            className="px-2 py-0.5 rounded text-xs uppercase tracking-wider mono"
            style={{ backgroundColor: `${successColor}22`, color: successColor }}
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

      <main className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            label="Mission Score"
            value={metrics.score}
            hint={payload.success ? 'Mission succeeded' : 'Mission failed'}
            color={successColor}
          />
          <MetricCard
            label="Samples Collected"
            value={metrics.samplesCollected}
            color={colors.accent}
          />
          <MetricCard
            label="Duration"
            value={`${metrics.duration} SOL`}
            hint={`out of ${payload.max_steps}`}
          />
          <MetricCard
            label="Distance Traveled"
            value={metrics.distance}
            hint="grid cells (Manhattan)"
          />
          <MetricCard
            label="Avg Energy"
            value={`${metrics.avgEnergy.toFixed(1)}%`}
            color={metrics.avgEnergy < 30 ? colors.danger : colors.text}
          />
          <MetricCard
            label="Avg Oxygen"
            value={`${metrics.avgOxygen.toFixed(1)}%`}
            color={metrics.avgOxygen < 40 ? colors.warning : colors.text}
          />
          <MetricCard
            label="Failures"
            value={metrics.failures}
            color={metrics.failures > 2 ? colors.danger : colors.text}
          />
          <MetricCard
            label="Peak Risk"
            value={`${(metrics.peakRisk * 100).toFixed(0)}%`}
            color={metrics.peakRisk > 0.7 ? colors.danger : colors.text}
          />
        </div>

        <ResourceChart
          title="Resource Levels Over Mission"
          data={data}
          series={[
            { key: 'energy', label: 'Energy', color: '#4db8ff' },
            { key: 'oxygen', label: 'Oxygen', color: '#3fb950' },
            { key: 'water', label: 'Water', color: '#79c0ff' },
            { key: 'food', label: 'Food', color: '#d29922' },
          ]}
        />

        <ResourceChart
          title="Component Health"
          data={data}
          series={[
            { key: 'battery', label: 'Battery', color: '#d29922' },
            { key: 'health', label: 'Rover Health', color: '#f85149' },
          ]}
        />

        <RiskChart data={data} />

        <FailureAnalysisPanel missionId={missionId} />
      </main>
    </div>
  );
}
