"""Deterministic negotiation logic for verified seller agents.

This module demonstrates the buyer-seller negotiation step without involving a
real LLM or external pricing engine. The logic is intentionally simple and
understandable for a hackathon sandbox.
"""

from __future__ import annotations

from typing import Any

from agents import SellerAgent


def negotiate_with_seller(seller: SellerAgent, buyer_budget: float) -> dict[str, Any]:
    """Simulate a deterministic negotiation round with a seller.

    Different seller agents behave differently based on their sandbox behavior
    profile. This keeps the demo understandable and very easy to expand.
    """
    # A buyer cannot make an offer above its declared maximum budget. The seller
    # may still counter above that budget; in that case the offer is reported but
    # explicitly marked as unaffordable rather than changing the seller's price.
    buyer_offer = min(
        buyer_budget,
        max(0, seller.initial_price - seller.buyer_offer_discount),
    )

    if seller.negotiation_style == "firm":
        seller_response = seller.initial_price
    elif seller.negotiation_style == "flexible":
        seller_response = max(seller.initial_price - seller.counter_discount, buyer_offer)
    else:
        seller_response = max(seller.initial_price - seller.counter_discount, buyer_offer)

    within_budget = seller_response <= buyer_budget

    return {
        "seller": seller.name,
        "initial_price": round(seller.initial_price, 2),
        "buyer_offer": round(buyer_offer, 2),
        "seller_response": round(seller_response, 2),
        "seller_counteroffer": round(seller_response, 2),
        # ``final_price`` is always the seller's actual final offer. It is never
        # capped at the buyer budget, because that would fabricate a deal.
        "final_price": round(seller_response, 2),
        "within_budget": within_budget,
        "verified": seller.verified,
    }
