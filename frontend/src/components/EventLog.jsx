const icons = {
  request: "→",
  discovery: "◌",
  verified: "✓",
  rejected: "×",
  negotiation: "↔",
  offer: "$",
  compare: "≡",
  selected: "✓",
  empty: "–",
};

export default function EventLog({ events, isRunning }) {
  return (
    <aside className="event-log" aria-labelledby="event-log-heading">
      <div className="event-log__header">
        <div>
          <div className="panel-kicker">Live trace</div>
          <h2 id="event-log-heading">Agent activity</h2>
        </div>
        <span className={isRunning ? "trace-indicator trace-indicator--live" : "trace-indicator"}>
          {isRunning ? "LIVE" : "TRACE"}
        </span>
      </div>

      <div className="event-log__body" aria-live="polite">
        {events.length === 0 ? (
          <div className="event-log__empty">
            <div className="event-log__empty-icon">⌁</div>
            <p>Run an agent to stream the marketplace decision trail.</p>
          </div>
        ) : (
          events.map((event) => (
            <div className={`event event--${event.kind}`} key={event.id}>
              <time>{event.time}</time>
              <span className="event__icon" aria-hidden="true">
                {icons[event.kind] || "·"}
              </span>
              <span>{event.message}</span>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}
