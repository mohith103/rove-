/**
 * AI Commander panel: current decision + reasoning + specialist votes.
 */
import type { Decision, MultiAgentDecision, SpecialistProposal } from '../types/mission';
import { SPECIALIST_COLORS } from '../types/mission';
import { colors, ui } from '../theme';

interface Props {
  decision: Decision | MultiAgentDecision | null;
}

function isMultiAgent(d: Decision | MultiAgentDecision | null): d is MultiAgentDecision {
  return !!d && 'multi_agent' in d && (d as MultiAgentDecision).multi_agent === true;
}

function ProposalRow({ p }: { p: SpecialistProposal }) {
  const color = SPECIALIST_COLORS[p.specialist] ?? colors.accent;
  return (
    <div className="flex items-start gap-2 text-xs py-1">
      <span
        className="inline-block px-1.5 py-0.5 rounded uppercase tracking-wider text-[10px] font-mono shrink-0"
        style={{ backgroundColor: `${color}22`, color }}
      >
        {p.specialist}
      </span>
      <span className="mono shrink-0" style={{ color: colors.textDim }}>
        {p.action}
      </span>
      <span className="shrink-0 mono" style={{ color }}>
        w={p.weight.toFixed(2)}
      </span>
      <span className="flex-1" style={{ color: colors.textDim }}>
        {p.rationale}
      </span>
    </div>
  );
}

export default function CommanderPanel({ decision }: Props) {
  const isMulti = isMultiAgent(decision);

  return (
    <div className={`${ui.panel} p-4 h-full overflow-y-auto`}>
      <div className="flex items-center justify-between mb-3">
        <h2 className={ui.panelTitle} style={{ marginBottom: 0 }}>
          AI Commander
        </h2>
        {isMulti && (
          <span
            className="text-[10px] uppercase tracking-widest px-2 py-0.5 rounded"
            style={{ backgroundColor: `${colors.accent}22`, color: colors.accent }}
          >
            Multi-Agent
          </span>
        )}
      </div>

      {!decision ? (
        <p className="text-xs" style={{ color: colors.textDim }}>
          Awaiting decision…
        </p>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className="px-2 py-0.5 rounded text-xs font-mono uppercase"
              style={{ backgroundColor: colors.accent2, color: '#fff' }}
            >
              {decision.explanation.action_name}
            </span>
            {!isMulti && 'overridden_by_planner' in decision && decision.overridden_by_planner && (
              <span
                className="px-2 py-0.5 rounded text-xs uppercase"
                style={{ backgroundColor: colors.warning, color: '#000' }}
              >
                Overridden
              </span>
            )}
          </div>

          <p className="text-sm leading-snug" style={{ color: colors.text }}>
            {decision.explanation.reason}
          </p>

          <div className="flex gap-4 text-xs">
            <div>
              <span style={{ color: colors.textDim }}>Confidence: </span>
              <span className="mono" style={{ color: colors.success }}>
                {(decision.explanation.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <div>
              <span style={{ color: colors.textDim }}>Risk: </span>
              <span className="mono" style={{ color: colors.warning }}>
                {(decision.explanation.risk_estimate * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          {isMulti && decision.proposals.length > 0 && (
            <div
              className="pt-2 mt-2 border-t"
              style={{ borderColor: colors.border }}
            >
              <div
                className="text-xs uppercase tracking-wider mb-1"
                style={{ color: colors.textDim }}
              >
                Specialist Votes
              </div>
              <div className="divide-y" style={{ borderColor: colors.border }}>
                {decision.proposals.map((p, i) => (
                  <ProposalRow key={i} p={p} />
                ))}
              </div>
            </div>
          )}

          {isMulti && decision.winning_specialists.length > 0 && (
            <div className="text-xs" style={{ color: colors.textDim }}>
              <span>Winning: </span>
              <span className="mono" style={{ color: colors.accent }}>
                {decision.winning_specialists.join(', ')}
              </span>
            </div>
          )}

          {!isMulti && 'factors' in decision.explanation && (
            <div
              className="pt-2 mt-2 border-t grid grid-cols-2 gap-x-4 gap-y-1 text-xs"
              style={{ borderColor: colors.border }}
            >
              {Object.entries(decision.explanation.factors).map(([k, v]) => (
                <div key={k} className="flex justify-between">
                  <span style={{ color: colors.textDim }}>{k}</span>
                  <span className="mono" style={{ color: colors.text }}>
                    {v}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
