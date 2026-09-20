import { useCallback, useEffect, useRef, useState } from "react";
import EventLog from "./components/EventLog";
import FinalDealCard from "./components/FinalDealCard";
import RequestPanel from "./components/RequestPanel";
import WorkflowDiagram from "./components/WorkflowDiagram";
import { runMarketplace } from "./lib/marketplace";

const initialForm = { item: "PS5", maxPrice: "500" };

function timestamp() {
  return new Intl.DateTimeFormat("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(new Date());
}

function displayPrice(amount) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(amount);
}

export default function App() {
  const [form, setForm] = useState(initialForm);
  const [activeRequest, setActiveRequest] = useState(null);
  const [result, setResult] = useState(null);
  const [events, setEvents] = useState([]);
  const [phase, setPhase] = useState("idle");
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState("");
  const timers = useRef([]);
  const runId = useRef(0);

  const clearTimeline = useCallback(() => {
    timers.current.forEach((timer) => window.clearTimeout(timer));
    timers.current = [];
  }, []);

  useEffect(() => clearTimeline, [clearTimeline]);

  const appendEvent = useCallback((kind, message) => {
    setEvents((current) => [
      ...current,
      { id: `${Date.now()}-${Math.random()}`, time: timestamp(), kind, message },
    ]);
  }, []);

  const playTimeline = useCallback((marketplaceResult, request, currentRun) => {
    const schedule = (delay, callback) => {
      const timer = window.setTimeout(() => {
        if (runId.current === currentRun) callback();
      }, delay);
      timers.current.push(timer);
    };

    const discovered = marketplaceResult.discovered_agents || [];
    const verification = marketplaceResult.verification || [];
    const negotiations = marketplaceResult.negotiations || [];
    let at = 0;

    setPhase("request");
    const requestBudget = Number(request.max_price ?? request.maxPrice ?? 0);
    appendEvent("request", `Buyer agent received ${request.item} with a ${displayPrice(requestBudget)} limit`);

    at += 420;
    schedule(at, () => {
      setPhase("discovery");
      if (discovered.length === 0) {
        appendEvent("empty", `No seller agents discovered for ${request.item}`);
      }
    });

    discovered.forEach((agent, index) => {
      schedule(at + 120 + index * 120, () => appendEvent("discovery", `Discovered ${agent.agent}`));
    });

    at += Math.max(620, discovered.length * 120 + 280);
    schedule(at, () => setPhase("verification"));

    verification.forEach((agent, index) => {
      schedule(at + 100 + index * 150, () => {
        appendEvent(
          agent.verified ? "verified" : "rejected",
          agent.verified
            ? `${agent.agent} verified via ANS`
            : `${agent.agent} rejected — identity not trusted`,
        );
      });
    });

    at += Math.max(620, verification.length * 150 + 300);
    schedule(at, () => setPhase("negotiation"));

    negotiations.forEach((negotiation, index) => {
      const start = at + 100 + index * 300;
      schedule(start, () => appendEvent("negotiation", `Negotiating with ${negotiation.seller}`));
      schedule(start + 150, () =>
        appendEvent("offer", `${negotiation.seller} → ${displayPrice(negotiation.final_price)}`),
      );
    });

    at += Math.max(680, negotiations.length * 300 + 260);
    schedule(at, () => {
      setPhase("compare");
      appendEvent("compare", `Comparing ${marketplaceResult.valid_offers.length} valid verified offer${marketplaceResult.valid_offers.length === 1 ? "" : "s"}`);
    });

    at += 560;
    schedule(at, () => {
      const selected = marketplaceResult.selected_deal;
      setPhase(selected ? "selected" : "empty");
      appendEvent(
        selected ? "selected" : "empty",
        selected
          ? `${selected.agent} selected at ${displayPrice(selected.final_price)}`
          : marketplaceResult.selection_reason,
      );
      setIsRunning(false);
    });
  }, [appendEvent]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const item = form.item.trim();
    const maxPrice = Number(form.maxPrice);

    clearTimeline();
    runId.current += 1;
    const currentRun = runId.current;
    setError("");
    setResult(null);
    setEvents([]);
    setPhase("request");
    setActiveRequest({ item, maxPrice });
    setIsRunning(true);
    appendEvent("request", `Buyer agent preparing ${item || "a request"}`);

    try {
      const marketplaceResult = await runMarketplace({ item, max_price: maxPrice });
      if (runId.current !== currentRun) return;

      setResult(marketplaceResult);
      setEvents([]);
      playTimeline(marketplaceResult, marketplaceResult.request, currentRun);
    } catch (requestError) {
      if (runId.current !== currentRun) return;

      setError(requestError.message);
      setPhase("idle");
      setIsRunning(false);
      appendEvent("rejected", "Marketplace API returned an error");
    }
  };

  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="brand" href="#top" aria-label="Agent Marketplace home">
          <span className="brand__mark" aria-hidden="true"><i /><i /><i /></span>
          <span>
            <strong>Agent Marketplace</strong>
            <small>Autonomous agent discovery, verification &amp; negotiation</small>
          </span>
        </a>
        <div className="header-status">
          <span className="header-status__pulse" />
          Sandbox network
        </div>
      </header>

      <main id="top" className="dashboard">
        <RequestPanel
          form={form}
          onChange={handleChange}
          onSubmit={handleSubmit}
          isRunning={isRunning}
          error={error}
        />

        <div className="dashboard-grid">
          <div className="workflow-column">
            <WorkflowDiagram
              result={result}
              phase={phase}
              activeRequest={activeRequest}
              isRunning={isRunning}
            />
            <FinalDealCard result={result} phase={phase} />
          </div>
          <EventLog events={events} isRunning={isRunning} />
        </div>
      </main>
    </div>
  );
}
