const money = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});

export default function FinalDealCard({ result, phase }) {
  const isComplete = phase === "selected" || phase === "empty";
  const deal = result?.selected_deal;

  if (!result) {
    return (
      <section className="deal-card deal-card--waiting" aria-label="Selected deal">
        <div className="panel-kicker">Final outcome</div>
        <h2>Selected deal</h2>
        <p>Awaiting a marketplace run.</p>
      </section>
    );
  }

  if (!isComplete) {
    return (
      <section className="deal-card deal-card--processing" aria-label="Selected deal processing">
        <div className="panel-kicker">Final outcome</div>
        <h2>Comparing verified offers</h2>
        <div className="deal-card__scanner" />
        <p>Trust and price checks are still in progress.</p>
      </section>
    );
  }

  if (!deal) {
    return (
      <section className="deal-card deal-card--empty" aria-label="No selected deal">
        <div className="panel-kicker">Final outcome</div>
        <h2>No verified deal selected</h2>
        <p>{result.selection_reason}</p>
      </section>
    );
  }

  return (
    <section className="deal-card deal-card--selected" aria-labelledby="selected-deal-heading">
      <div className="deal-card__eyebrow">
        <span className="selected-signal">✓</span>
        Selected deal
      </div>
      <div className="deal-card__main">
        <div>
          <h2 id="selected-deal-heading">{deal.agent}</h2>
          <p>{deal.capability}</p>
        </div>
        <strong>{money.format(deal.final_price)}</strong>
      </div>
      <div className="deal-card__checks">
        <span>✓ ANS verified</span>
        <span>✓ Within budget</span>
        <span>✓ Lowest valid offer</span>
      </div>
      <p className="deal-card__reason">{result.selection_reason}</p>
    </section>
  );
}
