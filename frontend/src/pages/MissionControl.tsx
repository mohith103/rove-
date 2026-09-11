/**
 * Top-level shell: Dashboard or Experiment Lab.
 */
import { useState } from 'react';

import CommanderPanel from '../components/CommanderPanel';
import EventFeed from '../components/EventFeed';
import MarsMap from '../components/MarsMap';
import MissionCompleteOverlay from '../components/MissionCompleteOverlay';
import MissionSetup from '../components/MissionSetup';
import ResourcePanel from '../components/ResourcePanel';
import TopBar from '../components/TopBar';
import AnalyticsPage from './AnalyticsPage';
import ExperimentLabPage from './ExperimentLabPage';
import ReplayPage from './ReplayPage';
import { useMissionStream } from '../hooks/useMissionStream';
import { api } from '../services/api';
import { colors } from '../theme';
import type {
  AgentName,
  Difficulty,
  MissionMode,
  MissionSummary,
  MissionStatus,
} from '../types/mission';

interface SetupConfig {
  difficulty: Difficulty;
  agent: AgentName;
  mode: MissionMode;
  seed: number;
  speed: number;
  max_steps?: number | null;
  map_size?: number | null;
  multi_agent?: boolean;
}

type SubPage = 'dashboard' | 'replay' | 'analytics';
type RootTab = 'dashboard' | 'lab';

export default function MissionControl() {
  const [tab, setTab] = useState<RootTab>('dashboard');
  const [mission, setMission] = useState<MissionSummary | null>(null);
  const [config, setConfig] = useState<SetupConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overlayDismissed, setOverlayDismissed] = useState(false);
  const [subPage, setSubPage] = useState<SubPage>('dashboard');

  const stream = useMissionStream(mission?.id ?? null);

  async function launchMission(cfg: SetupConfig) {
    setLoading(true);
    setError(null);
    setOverlayDismissed(false);
    setSubPage('dashboard');
    try {
      const summary = await api.createMission({
        difficulty: cfg.difficulty,
        agent: cfg.agent,
        mode: cfg.mode,
        seed: cfg.seed,
        speed: cfg.speed,
        max_steps: cfg.max_steps ?? null,
        map_size: cfg.map_size ?? null,
        multi_agent: cfg.multi_agent ?? false,
      });
      setConfig(cfg);
      setMission(summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function handlePause() {
    if (!mission) return;
    try { await api.pauseMission(mission.id); }
    catch (err) { setError(err instanceof Error ? err.message : String(err)); }
  }

  async function handleResume() {
    if (!mission) return;
    try { await api.resumeMission(mission.id); }
    catch (err) { setError(err instanceof Error ? err.message : String(err)); }
  }

  function backToSetup() {
    setMission(null);
    setConfig(null);
    setError(null);
    setOverlayDismissed(false);
    setSubPage('dashboard');
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: colors.bg }}>
      <nav
        className="flex items-center gap-1 px-4 py-2 border-b shrink-0"
        style={{ backgroundColor: colors.surface, borderColor: colors.border }}
      >
        <span className="text-xl font-bold tracking-[0.2em] mr-6" style={{ color: colors.accent }}>
          ROVE
        </span>
        <button
          onClick={() => setTab('dashboard')}
          className="px-3 py-1 rounded text-xs uppercase tracking-wider"
          style={{
            backgroundColor: tab === 'dashboard' ? colors.surface2 : 'transparent',
            color: tab === 'dashboard' ? colors.text : colors.textDim,
          }}
        >
          Dashboard
        </button>
        <button
          onClick={() => setTab('lab')}
          className="px-3 py-1 rounded text-xs uppercase tracking-wider"
          style={{
            backgroundColor: tab === 'lab' ? colors.surface2 : 'transparent',
            color: tab === 'lab' ? colors.text : colors.textDim,
          }}
        >
          Experiment Lab
        </button>
      </nav>

      <div className="flex-1 flex flex-col min-h-0">
        {tab === 'lab' ? (
          <div className="flex-1 overflow-y-auto p-4">
            <ExperimentLabPage />
          </div>
        ) : mission && subPage === 'replay' ? (
          <ReplayPage missionId={mission.id} onExit={() => setSubPage('dashboard')} />
        ) : mission && subPage === 'analytics' ? (
          <AnalyticsPage missionId={mission.id} onExit={() => setSubPage('dashboard')} />
        ) : !mission || !config ? (
          <MissionSetup onLaunch={launchMission} loading={loading} error={error} />
        ) : (
          <>
            <TopBar
              sol={stream.state?.step ?? mission.step ?? 0}
              maxSol={mission.max_steps}
              connected={stream.connected}
              status={(stream.status ?? mission.status) as MissionStatus}
              agentName={mission.multi_agent ? 'multi-agent' : config.agent}
              difficulty={config.difficulty}
              speed={config.speed}
              onPause={handlePause}
              onResume={handleResume}
              onNewMission={backToSetup}
            />

            {error && (
              <div
                className="m-4 p-3 rounded text-sm"
                style={{
                  backgroundColor: `${colors.danger}22`,
                  border: `1px solid ${colors.danger}`,
                  color: colors.danger,
                }}
              >
                {error}
              </div>
            )}

            <main className="flex-1 grid gap-4 p-4 grid-cols-1 lg:grid-cols-3 items-stretch">
              <div className="lg:col-span-2 h-[560px]">
                <MarsMap state={stream.state} />
              </div>

              <div className="flex flex-col gap-4 h-[560px]">
                <div className="flex-1 min-h-0">
                  <CommanderPanel decision={stream.decision} />
                </div>
                <div className="flex-1 min-h-0">
                  <ResourcePanel rover={stream.state?.rover ?? null} />
                </div>
              </div>

              <div className="lg:col-span-3 h-[220px]">
                <EventFeed events={stream.events} />
              </div>
            </main>

            {stream.status === 'done' && stream.state && !overlayDismissed && (
              <MissionCompleteOverlay
                state={stream.state}
                status={(stream.status ?? mission.status) as MissionStatus}
                onClose={() => setOverlayDismissed(true)}
                onNewMission={backToSetup}
                onReplay={() => { setSubPage('replay'); setOverlayDismissed(true); }}
                onAnalytics={() => { setSubPage('analytics'); setOverlayDismissed(true); }}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
