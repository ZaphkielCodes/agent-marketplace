"""Seller agent definitions for the sandbox marketplace.

This module intentionally contains simulated seller agents only. The goal is to
model the Marketplace demo flow without pretending to integrate real seller
APIs or real companies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SellerAgent:
    """A simulated seller agent participating in the marketplace sandbox."""

    name: str
    product: str
    initial_price: float
    verified: bool
    ans_id: str
    capabilities: list[str] = field(default_factory=list)
    buyer_offer_discount: int = 0
    counter_discount: int = 0
    negotiation_style: str = "standard"
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.capabilities:
            self.capabilities = [self.product]
        self.capabilities = [cap.lower() for cap in self.capabilities]

    def matches_capability(self, item: str) -> bool:
        target = (item or "").strip().lower()
        return target in self.capabilities

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.name,
            "product": self.product,
            "capabilities": self.capabilities,
            "initial_price": self.initial_price,
            "verified": self.verified,
            "ans_id": self.ans_id,
            "negotiation_style": self.negotiation_style,
            "notes": self.notes,
        }

    def to_discovery_dict(self, item: str) -> dict[str, Any]:
        return {
            "agent": self.name,
            "capability": item.strip().lower(),
            "product": self.product,
            "initial_price": self.initial_price,
            "verified": self.verified,
            "ans_id": self.ans_id,
        }


SELLER_CATALOG: list[SellerAgent] = [
    SellerAgent(
        name="TechBot",
        product="PS5",
        initial_price=499,
        verified=True,
        ans_id="ans_demo_001",
        capabilities=["PS5", "gaming laptop"],
        buyer_offer_discount=29,
        counter_discount=19,
        negotiation_style="standard",
        notes="Verified sandbox seller with a stable but slightly premium offer.",
    ),
    SellerAgent(
        name="GameHubBot",
        product="PS5",
        initial_price=475,
        verified=True,
        ans_id="ans_demo_002",
        capabilities=["PS5", "monitor"],
        buyer_offer_discount=15,
        counter_discount=10,
        negotiation_style="standard",
        notes="Verified sandbox seller with a slightly better value than TechBot.",
    ),
    SellerAgent(
        name="BestDealBot",
        product="PS5",
        initial_price=450,
        verified=False,
        ans_id="ans_demo_003",
        capabilities=["PS5", "headphones"],
        buyer_offer_discount=25,
        counter_discount=15,
        negotiation_style="standard",
        notes="Low-price seller that is intentionally unverified for trust testing.",
    ),
    SellerAgent(
        name="PulseLaptopBot",
        product="gaming laptop",
        initial_price=1200,
        verified=True,
        ans_id="ans_demo_004",
        capabilities=["gaming laptop", "monitor"],
        buyer_offer_discount=120,
        counter_discount=90,
        negotiation_style="flexible",
        notes="Verified seller with flexible pricing on premium devices.",
    ),
    SellerAgent(
        name="AudioNestBot",
        product="headphones",
        initial_price=220,
        verified=True,
        ans_id="ans_demo_005",
        capabilities=["headphones", "monitor"],
        buyer_offer_discount=25,
        counter_discount=18,
        negotiation_style="standard",
        notes="Verified audio seller with a reasonable negotiation range.",
    ),
    SellerAgent(
        name="DisplayWorksBot",
        product="monitor",
        initial_price=330,
        verified=True,
        ans_id="ans_demo_006",
        capabilities=["monitor"],
        buyer_offer_discount=30,
        counter_discount=20,
        negotiation_style="firm",
        notes="Verified display seller that does not move much on price.",
    ),
    SellerAgent(
        name="CheapAudioBot",
        product="headphones",
        initial_price=180,
        verified=False,
        ans_id="ans_demo_007",
        capabilities=["headphones"],
        buyer_offer_discount=30,
        counter_discount=25,
        negotiation_style="standard",
        notes="Cheaper headphones seller, but intentionally unverified in the sandbox.",
    ),
]


def discover_sellers(item: str) -> list[SellerAgent]:
    """Return seller agents whose primary product matches the requested item.

    This is where the real marketplace would later query a directory or registry
    of seller agents. For the sandbox, it is a simple in-memory catalog.
    """
    target = (item or "").strip().lower()
    return [seller for seller in SELLER_CATALOG if seller.product.strip().lower() == target]


def get_seller_by_name(name: str) -> SellerAgent | None:
    for seller in SELLER_CATALOG:
        if seller.name.lower() == name.lower():
            return seller
    return None
