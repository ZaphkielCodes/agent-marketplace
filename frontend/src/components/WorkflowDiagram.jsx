const money = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});

const phases = ["idle", "request", "discovery", "verification", "negotiation", "compare", "selected", "empty"];

function phaseReached(currentPhase, targetPhase) {
  const current = phases.indexOf(currentPhase);
  const target = phases.indexOf(targetPhase);
  return current >= target || currentPhase === "empty";
}

function verificationByAgent(result) {
  return new Map((result?.verification || []).map((entry) => [entry.agent, entry]));
}

function negotiationByAgent(result) {
  return new Map((result?.negotiations || []).map((entry) => [entry.seller, entry]));
}

export default function WorkflowDiagram({ result, phase, activeRequest, isRunning }) {
  const agents = result?.discovered_agents || [];
  const verification = verificationByAgent(result);
  const negotiations = negotiationByAgent(result);
  const hasRun = Boolean(activeRequest);
  const showDiscovery = result && phaseReached(phase, "discovery");
  const showVerification = result && phaseReached(phase, "verification");
  const showNegotiation = result && phaseReached(phase, "negotiation");
  const showCompare = result && phaseReached(phase, "compare");
  const showSelection = result && (phase === "selected" || phase === "empty");

  return (
    <section className="workflow" aria-labelledby="workflow-heading">
      <div className="workflow__header">
        <div>
          <div className="panel-kicker">Autonomous workflow</div>
          <h2 id="workflow-heading">Decision graph</h2>
        </div>
        <div className="workflow__legend" aria-label="Verification legend">
          <span><i className="legend-dot legend-dot--verified" /> Verified</span>
          <span><i className="legend-dot legend-dot--rejected" /> Rejected</span>
        </div>
      </div>

      <div className="process-rail" aria-label="Marketplace workflow stages">
        {[
          ["request", "Buyer"],
          ["discovery", "Discover"],
          ["verification", "Verify"],
          ["negotiation", "Negotiate"],
          ["compare", "Compare"],
          ["selected", "Select"],
        ].map(([stage, label], index) => (
          <div className="process-rail__step" key={stage}>
            <span className={phaseReached(phase, stage) ? "process-rail__dot is-active" : "process-rail__dot"}>
              {String(index + 1).padStart(2, "0")}
            </span>
            <span>{label}</span>
          </div>
        ))}
      </div>

      <div className={isRunning ? "workflow-canvas workflow-canvas--running" : "workflow-canvas"}>
        <div className={hasRun ? "flow-node flow-node--buyer is-visible" : "flow-node flow-node--buyer"}>
          <NodeGlyph type="buyer" />
          <div>
            <span className="node-label">Buyer agent</span>
            <strong>{activeRequest ? `Find ${activeRequest.item}` : "Ready for a request"}</strong>
            <small>{activeRequest ? `Budget ${money.format(activeRequest.maxPrice)}` : "Set a target above"}</small>
          </div>
        </div>

        <FlowLine active={phaseReached(phase, "discovery")} />

        <div className={showDiscovery ? "flow-node flow-node--discovery is-visible" : "flow-node flow-node--discovery"}>
          <NodeGlyph type="search" />
          <div>
            <span className="node-label">Discovery</span>
            <strong>{showDiscovery ? `${agents.length} seller agent${agents.length === 1 ? "" : "s"}` : "Scanning catalog"}</strong>
            <small>Product-matched sellers</small>
          </div>
        </div>

        {result && agents.length === 0 && showDiscovery && (
          <div className="no-agents-state">
            <span>⌁</span>
            <div>
              <strong>No seller agents found</strong>
              <p>The discovery stage returned no product-matched sellers.</p>
            </div>
          </div>
        )}

        {agents.length > 0 && (
          <>
            <div className={showDiscovery ? "branch-connector is-active" : "branch-connector"} />
            <div className={showDiscovery ? "seller-grid is-visible" : "seller-grid"}>
              {agents.map((agent, index) => {
                const identity = verification.get(agent.agent);
                const deal = negotiations.get(agent.agent);
                const isVerified = identity?.verified;
                const trustClass = showVerification
                  ? isVerified
                    ? "agent-card--verified"
                    : "agent-card--rejected"
                  : "agent-card--pending";
                const selected = result?.selected_deal?.agent === agent.agent && showSelection;

                return (
                  <article
                    className={`agent-card ${trustClass} ${selected ? "agent-card--selected" : ""}`}
                    key={agent.agent}
                    style={{ "--card-delay": `${index * 90}ms` }}
                  >
                    <div className="agent-card__topline">
                      <span className="agent-index">A{String(index + 1).padStart(2, "0")}</span>
                      <span className="agent-price">{money.format(agent.initial_price)}</span>
                    </div>
                    <h3>{agent.agent}</h3>
                    <p>{agent.product}</p>

                    <div className={showVerification ? `identity-chip ${isVerified ? "identity-chip--verified" : "identity-chip--rejected"}` : "identity-chip"}>
                      {showVerification ? (isVerified ? "✓ ANS verified" : "× identity rejected") : "ANS check pending"}
                    </div>

                    <div className={showNegotiation ? `agent-card__outcome ${isVerified ? "agent-card__outcome--negotiation" : "agent-card__outcome--rejected"}` : "agent-card__outcome"}>
                      {showNegotiation && isVerified && deal ? (
                        <>
                          <span>Negotiated</span>
                          <strong>{money.format(deal.final_price)}</strong>
                          <small>{deal.within_budget ? "Within budget" : "Over budget"}</small>
                        </>
                      ) : showNegotiation && !isVerified ? (
                        <>
                          <span>Route closed</span>
                          <strong>Rejected</strong>
                          <small>Not eligible to negotiate</small>
                        </>
                      ) : (
                        <span>{isVerified ? "Queued for negotiation" : "Awaiting identity check"}</span>
                      )}
                    </div>
                  </article>
                );
              })}
            </div>
          </>
        )}

        {result && agents.length > 0 && (
          <>
            <div className={showCompare ? "merge-connector is-active" : "merge-connector"} />
            <div className={showCompare ? "flow-node flow-node--compare is-visible" : "flow-node flow-node--compare"}>
              <NodeGlyph type="compare" />
              <div>
                <span className="node-label">Compare valid offers</span>
                <strong>{showCompare ? `${result.valid_offers.length} valid offer${result.valid_offers.length === 1 ? "" : "s"}` : "Evaluating trust + price"}</strong>
                <small>Verified agents only</small>
              </div>
            </div>
            <FlowLine active={showSelection} />
            <div className={showSelection ? `selection-node ${result.selected_deal ? "selection-node--success" : "selection-node--empty"} is-visible` : "selection-node"}>
              <span>{result.selected_deal ? "✓" : "–"}</span>
              <div>
                <strong>{result.selected_deal ? "Verified deal selected" : "No valid deal"}</strong>
                <small>{result.selected_deal ? result.selected_deal.agent : "No offer met the required checks"}</small>
              </div>
            </div>
          </>
        )}
      </div>
    </section>
  );
}

function FlowLine({ active }) {
  return <div className={active ? "flow-line is-active" : "flow-line"} aria-hidden="true" />;
}

function NodeGlyph({ type }) {
  const glyphs = {
    buyer: "◈",
    search: "⌕",
    compare: "⇄",
  };
  return <span className="node-glyph" aria-hidden="true">{glyphs[type]}</span>;
}
