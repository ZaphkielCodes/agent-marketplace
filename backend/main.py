"""FastAPI backend for the AI Agent Marketplace sandbox.

This is a sandbox-only demo. It is intentionally designed to model the flow:

USER REQUEST
↓
BUYER AGENT
↓
DISCOVER SELLERS
↓
CHECK SIMULATED ANS IDENTITY
↓
REJECT UNVERIFIED AGENTS
↓
NEGOTIATE WITH VERIFIED SELLERS
↓
COMPARE FINAL OFFERS
↓
SELECT VALID DEAL
↓
RETURN RESULTS

The simulated ANS logic is isolated in ans.py so it can later be replaced with
real GoDaddy ANS integration without rewriting the marketplace logic.
"""

from __future__ import annotations

import math
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator

from agents import discover_sellers, get_seller_by_name
from ans import verify_ans
from negotiation import negotiate_with_seller


class RunRequest(BaseModel):
    """Validated buyer request accepted by the marketplace endpoint."""

    item: str = Field(..., min_length=1, max_length=120)
    max_price: float = Field(..., gt=0)

    @validator("item")
    def normalize_item(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("item must contain non-whitespace characters")
        return normalized

    @validator("max_price", pre=True)
    def reject_boolean_price(cls, value: Any) -> Any:
        if isinstance(value, bool):
            raise ValueError("max_price must be a number, not a boolean")
        return value

    @validator("max_price")
    def require_finite_price(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("max_price must be finite")
        return value

    class Config:
        extra = "forbid"


app = FastAPI(
    title="AI Agent Marketplace Sandbox",
    version="0.2.0",
    description="A deterministic, sandbox-only marketplace workflow.",
)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "service": "ai-agent-marketplace-sandbox"}


@app.get("/agents/gamehub")
async def gamehub_agent() -> dict[str, str]:
    """Expose the existing GameHubBot seller's public availability details."""
    seller = get_seller_by_name("GameHubBot")
    if seller is None:
        raise HTTPException(status_code=404, detail="GameHubBot is unavailable.")

    return {
        "agent": seller.name,
        "product": seller.product,
        "capability": seller.product.strip().lower(),
        "status": "available",
    }


@app.post("/run")
async def run_marketplace(request: RunRequest) -> dict[str, Any]:
    """Execute the marketplace workflow for a buyer request.

    The logical flow is intentionally straightforward and easy to understand for a
    hackathon demo: discover sellers, verify their sandbox ANS identity,
    reject invalid sellers, negotiate with verified sellers, compare final offers,
    and choose the best valid deal within the buyer budget.
    """
    item = request.item
    buyer_budget = request.max_price

    discovered_agents = discover_sellers(item)
    discovered_payload = [seller.to_discovery_dict(item) for seller in discovered_agents]

    verification_results = [verify_ans(seller) for seller in discovered_agents]
    rejected_agents = [result for result in verification_results if not result["verified"]]

    negotiations: list[dict[str, Any]] = []
    valid_offers: list[dict[str, Any]] = []

    for seller, verification in zip(discovered_agents, verification_results):
        if not verification["verified"]:
            continue

        negotiation = negotiate_with_seller(seller, buyer_budget)
        negotiations.append(negotiation)

        if negotiation["within_budget"]:
            valid_offers.append(
                {
                    "agent": negotiation["seller"],
                    "capability": item.lower(),
                    "final_price": negotiation["final_price"],
                    "verified": True,
                    "ans_id": verification["ans_id"],
                    "seller_response": negotiation["seller_response"],
                }
            )

    valid_offers.sort(key=lambda offer: (offer["final_price"], offer["agent"].casefold()))

    selected_deal = None
    selected_reason = None

    if not discovered_agents:
        selected_reason = f"No seller agents were discovered for '{item}'."
    elif not valid_offers:
        selected_reason = (
            f"No valid verified offers were found for '{item}' within the buyer budget of "
            f"${buyer_budget:.2f}."
        )
    else:
        selected_deal = valid_offers[0]
        selected_reason = (
            f"Selected {selected_deal['agent']} because it is the lowest verified "
            f"offer for '{item}' within budget."
        )

    return {
        "request": {
            "item": item,
            "max_price": buyer_budget,
        },
        "discovered_agents": discovered_payload,
        "verification": verification_results,
        "rejected_agents": rejected_agents,
        "negotiations": negotiations,
        "valid_offers": valid_offers,
        "selected_deal": selected_deal,
        "selection_reason": selected_reason,
    }
