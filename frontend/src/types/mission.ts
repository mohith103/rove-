/**
 * TypeScript types mirroring the FastAPI backend schemas.
 * Keep these in sync with `backend/app/schemas/mission.py`.
 */

export type Difficulty = 'default' | 'easy' | 'medium' | 'hard' | 'extreme';
export type AgentName = 'random' | 'rule_based' | 'ppo';
export type MissionMode = 'science' | 'survival' | 'exploration' | 'balanced';
export type MissionStatus = 'running' | 'paused' | 'done';

// ---------- Requests ----------

export interface CreateMissionRequest {
  difficulty: Difficulty;
  agent: AgentName;
  mode: MissionMode;
  seed: number;
  model_path?: string | null;
  speed: number;
}

// ---------- Responses ----------

export interface MissionSummary {
  id: string;
  difficulty: Difficulty;
  agent: AgentName;
  mode: MissionMode;
  seed: number;
  status: MissionStatus;
  step: number;
  max_steps: number;
  success: boolean;
  failure_reason: string | null;
  multi_agent?: boolean;
}

export interface RoverState {
  x: number;
  y: number;
  energy: number;
  water: number;
  oxygen: number;
  food: number;
  battery_health: number;
  rover_health: number;
  communication: number;
  temperature: number;
  samples_collected: number;
  cargo: string[];
  current_task: string;
  status: string;
}

export interface BaseState {
  x: number;
  y: number;
  recharge_rate: number;
}

export interface ScienceSite {
  x: number;
  y: number;
  value: number;
  difficulty: number;
  sample_type: string;
  collected: boolean;
}

export interface WorldState {
  step: number;
  max_steps: number;
  rover: RoverState;
  base: BaseState;
  science_sites: ScienceSite[];
  done: boolean;
  success: boolean;
  failure_reason: string | null;
  events: string[];
  terrain: number[][];
  width: number;
  height: number;
}

export interface Explanation {
  action: number;
  action_name: string;
  reason: string;
  factors: Record<string, string>;
  confidence: number;
  risk_estimate: number;
  is_from_neural_net: boolean;
}

export interface PlanInfo {
  name: string;
  expected_science: number;
  expected_energy_cost: number;
  expected_risk: number;
  steps: number;
  action: number;
  notes: string;
}

export interface Decision {
  action: number;
  explanation: Explanation;
  chosen_plan: PlanInfo | null;
  plan_scores: [string, number][];
  overridden_by_planner: boolean;
}

export interface MissionDetail {
  id: string;
  difficulty: Difficulty;
  agent: AgentName;
  mode: MissionMode;
  seed: number;
  status: MissionStatus;
  state: WorldState;
  decision: Decision | null;
  events: string[];
}

// ---------- WebSocket payloads ----------

export interface StreamPayload {
  summary?: MissionSummary;
  state?: WorldState;
  last_decision?: Decision | null;
  status?: 'done';
  error?: string;
}

// ---------- Meta ----------

export interface AgentInfo {
  name: AgentName;
  description: string;
}

export interface ModelsResponse {
  agents: AgentInfo[];
}

export const ACTION_NAMES: Record<number, string> = {
  0: 'MOVE_NORTH',
  1: 'MOVE_SOUTH',
  2: 'MOVE_EAST',
  3: 'MOVE_WEST',
  4: 'COLLECT_SAMPLE',
  5: 'ANALYZE_SAMPLE',
  6: 'RETURN_TO_BASE',
  7: 'RECHARGE',
  8: 'REPAIR',
  9: 'COMMUNICATE',
  10: 'WAIT',
};

// ---------- Terrain ----------

export enum TerrainType {
  PLAIN = 0,
  ROCK = 1,
  CRATER = 2,
  MOUNTAIN = 3,
  SAND = 4,
  BASE = 5,
  SCIENCE_SITE = 6,
}

export const TERRAIN_COLORS: Record<TerrainType, string> = {
  [TerrainType.PLAIN]: '#2a1f1a',
  [TerrainType.ROCK]: '#5a3a2a',
  [TerrainType.CRATER]: '#3d2a24',
  [TerrainType.MOUNTAIN]: '#1a1a1f',
  [TerrainType.SAND]: '#4a3524',
  [TerrainType.BASE]: '#4db8ff',
  [TerrainType.SCIENCE_SITE]: '#d29922',
};

export const TERRAIN_LABELS: Record<TerrainType, string> = {
  [TerrainType.PLAIN]: 'Plain',
  [TerrainType.ROCK]: 'Rock',
  [TerrainType.CRATER]: 'Crater',
  [TerrainType.MOUNTAIN]: 'Mountain',
  [TerrainType.SAND]: 'Sand',
  [TerrainType.BASE]: 'Base',
  [TerrainType.SCIENCE_SITE]: 'Science Site',
};

// ---------- Map interactions ----------

export interface HoverCell {
  x: number;
  y: number;
}

export interface TrailPoint {
  x: number;
  y: number;
}

// ---------- Replay ----------

export interface ReplayFrame {
  step: number;
  rover: RoverState;
  base: BaseState;
  science_sites: ScienceSite[];
  done: boolean;
  success: boolean;
  failure_reason: string | null;
}

export interface ReplayPayload {
  id: string;
  difficulty: Difficulty;
  agent: AgentName;
  mode: MissionMode;
  seed: number;
  status: MissionStatus;
  success: boolean;
  failure_reason: string | null;
  max_steps: number;
  width: number;
  height: number;
  terrain: number[][];
  frames: ReplayFrame[];
  decisions: (Decision | null)[];
  events: string[];
}

// ---------- Experiments ----------

export interface RunExperimentRequest {
  agents: AgentName[];
  difficulties: Difficulty[];
  mode: MissionMode;
  episodes: number;
  seed: number;
  max_steps?: number | null;
}

export interface ExperimentRow {
  agent: string;
  difficulty: string;
  episodes: number;
  success_rate: number;
  avg_samples: number;
  avg_steps: number;
  avg_energy_left: number;
  avg_oxygen_left: number;
  avg_reward: number;
  top_failure: string;
}

export interface RunExperimentResponse {
  rows: ExperimentRow[];
  total_missions: number;
  elapsed_seconds: number;
}


// ---------- Counterfactual ----------

export type OverrideType =
  | 'force_return_to_base'
  | 'force_recharge'
  | 'force_repair'
  | 'force_wait'
  | 'custom_action';

export interface RunCounterfactualRequest {
  fork_step: number;
  override: OverrideType;
  override_duration: number;
  custom_action?: number | null;
}

export interface TimelineFrame {
  step: number;
  rover: RoverState;
  base: BaseState;
  science_sites: ScienceSite[];
  done: boolean;
  success: boolean;
  failure_reason: string | null;
}

export interface CounterfactualTimeline {
  label: string;
  description: string;
  success: boolean;
  steps: number;
  samples_collected: number;
  energy_left: number;
  oxygen_left: number;
  rover_health: number;
  failure_reason: string | null;
  frames: TimelineFrame[];
}

export interface RunCounterfactualResponse {
  mission_id: string;
  fork_step: number;
  override: string;
  override_duration: number;
  actual: CounterfactualTimeline;
  counterfactual: CounterfactualTimeline;
  verdict: string;
}
// ---------- Failure Analysis ----------

export interface CriticalMoment {
  step: number;
  label: string;
  detail: string;
  severity: 'info' | 'warning' | 'critical';
}

export interface AnalysisResponse {
  mission_id: string;
  success: boolean;
  primary_cause: string;
  contributing_factors: string[];
  recommendations: string[];
  critical_moments: CriticalMoment[];
  summary: string;
}

// ---------- Multi-Agent ----------

export interface SpecialistProposal {
  specialist: string;
  action: number;
  weight: number;
  rationale: string;
}

export interface MultiAgentDecision {
  action: number;
  explanation: Explanation;
  proposals: SpecialistProposal[];
  action_scores: Record<string, number>;
  winning_specialists: string[];
  multi_agent: true;
}

export const SPECIALIST_COLORS: Record<string, string> = {
  navigation: '#4db8ff',
  science: '#d29922',
  safety: '#f85149',
  resource: '#3fb950',
};
