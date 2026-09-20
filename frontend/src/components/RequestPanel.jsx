export default function RequestPanel({ form, onChange, onSubmit, isRunning, error }) {
  return (
    <section className="request-panel" aria-labelledby="request-heading">
      <div className="panel-kicker">Mission control</div>
      <div className="request-panel__title-row">
        <div>
          <h2 id="request-heading">Launch a buyer agent</h2>
          <p>Set the target and budget. The marketplace handles the agent workflow.</p>
        </div>
        <div className={isRunning ? "live-status live-status--running" : "live-status"}>
          <span className="live-status__dot" />
          {isRunning ? "Agents processing" : "Ready"}
        </div>
      </div>

      <form className="request-form" onSubmit={onSubmit}>
        <label className="field field--item">
          <span>What are you looking for?</span>
          <input
            name="item"
            value={form.item}
            onChange={onChange}
            placeholder="e.g. PS5"
            autoComplete="off"
            disabled={isRunning}
            required
          />
        </label>

        <label className="field field--price">
          <span>Maximum price</span>
          <div className="price-input">
            <span aria-hidden="true">$</span>
            <input
              name="maxPrice"
              type="number"
              value={form.maxPrice}
              onChange={onChange}
              min="0.01"
              step="0.01"
              inputMode="decimal"
              disabled={isRunning}
              required
            />
          </div>
        </label>

        <button className="run-button" type="submit" disabled={isRunning}>
          {isRunning ? <span className="button-spinner" aria-hidden="true" /> : <RunIcon />}
          {isRunning ? "Running agents" : "Run agent"}
        </button>
      </form>

      {error && (
        <div className="api-error" role="alert">
          <span>!</span>
          <div>
            <strong>Marketplace run failed</strong>
            <p>{error}</p>
          </div>
        </div>
      )}
    </section>
  );
}

function RunIcon() {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true">
      <path d="M4 3.8 16.2 10 4 16.2V3.8Z" fill="currentColor" />
    </svg>
  );
}
