"""GoDaddy ANS verification with a deterministic sandbox fallback."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from agents import SellerAgent

DEFAULT_ANS_BASE_URL = "https://api.godaddy.com"
ANS_TIMEOUT_SECONDS = 10.0

logger = logging.getLogger(__name__)


def _verify_sandbox_ans(seller: SellerAgent) -> dict[str, Any]:
    """Simulate the identity verification status for a seller agent.

    This function does not require a domain or make external network calls.
    It checks the seller agent's existing sandbox verification state.
    """
    if seller.verified:
        return {
            "agent": seller.name,
            "ans_id": seller.ans_id,
            "verified": True,
            "status": "VERIFIED",
        }

    return {
        "agent": seller.name,
        "ans_id": seller.ans_id,
        "verified": False,
        "status": "UNVERIFIED",
        "reason": "Sandbox ANS check failed: seller identity is not trusted.",
    }


def _live_failure(seller: SellerAgent, reason: str) -> dict[str, Any]:
    """Return a frontend-compatible failed verification result."""
    return {
        "agent": seller.name,
        "ans_id": seller.ans_id,
        "verified": False,
        "status": "UNVERIFIED",
        "source": "godaddy_ans",
        "reason": reason,
    }


def _verify_live_ans(seller: SellerAgent) -> dict[str, Any]:
    """Verify a seller against the documented GoDaddy registered-agent API."""
    godaddy_key = os.getenv("GODADDY_KEY", "").strip()
    godaddy_secret = os.getenv("GODADDY_SECRET", "").strip()
    if not godaddy_key or not godaddy_secret:
        logger.warning("ANS identity rejected: GODADDY_KEY and/or GODADDY_SECRET are missing")
        return _live_failure(seller, "GODADDY_KEY and GODADDY_SECRET are required when ANS_MODE=live.")

    ans_id = seller.ans_id
    if not isinstance(ans_id, str) or not ans_id.strip():
        logger.warning("ANS identity rejected for seller=%s: missing ANS ID", seller.name)
        return _live_failure(seller, "Seller is missing an ANS agent ID.")

    base_url = os.getenv("GODADDY_ANS_BASE_URL", DEFAULT_ANS_BASE_URL).strip()
    base_url = (base_url or DEFAULT_ANS_BASE_URL).rstrip("/")
    url = f"{base_url}/v1/agents/{ans_id}"
    headers = {
        "Authorization": f"sso-key {godaddy_key}:{godaddy_secret}",
        "Accept": "application/json",
    }

    logger.info("ANS lookup started for seller=%s ans_id=%s", seller.name, ans_id)
    try:
        response = httpx.get(url, headers=headers, timeout=ANS_TIMEOUT_SECONDS)
    except httpx.TimeoutException:
        logger.warning("ANS request failed for seller=%s: timeout", seller.name)
        return _live_failure(seller, "GoDaddy ANS request timed out.")
    except httpx.RequestError as exc:
        logger.warning("ANS request failed for seller=%s: %s", seller.name, exc.__class__.__name__)
        return _live_failure(seller, "GoDaddy ANS request failed due to a network error.")

    if response.status_code == 401:
        logger.warning("ANS request failed for seller=%s: HTTP 401", seller.name)
        return _live_failure(seller, "GoDaddy ANS authentication failed (401).")
    if response.status_code == 403:
        logger.warning("ANS request failed for seller=%s: HTTP 403", seller.name)
        return _live_failure(seller, "GoDaddy ANS authorization failed (403).")
    if response.status_code == 404:
        logger.warning("ANS request failed for seller=%s: HTTP 404", seller.name)
        return _live_failure(seller, "GoDaddy ANS registered agent was not found (404).")
    if response.status_code == 429:
        logger.warning("ANS request failed for seller=%s: HTTP 429", seller.name)
        return _live_failure(seller, "GoDaddy ANS rate limit exceeded (429).")
    if response.status_code >= 500:
        logger.warning("ANS request failed for seller=%s: HTTP %s", seller.name, response.status_code)
        return _live_failure(seller, "GoDaddy ANS service is unavailable.")
    if not response.is_success:
        logger.warning("ANS request failed for seller=%s: HTTP %s", seller.name, response.status_code)
        return _live_failure(seller, f"GoDaddy ANS returned HTTP {response.status_code}.")

    try:
        payload = response.json()
    except (TypeError, ValueError):
        logger.warning("ANS identity rejected for seller=%s: malformed JSON", seller.name)
        return _live_failure(seller, "GoDaddy ANS returned malformed JSON.")

    if not isinstance(payload, dict):
        logger.warning("ANS identity rejected for seller=%s: unexpected JSON shape", seller.name)
        return _live_failure(seller, "GoDaddy ANS response has an unexpected JSON shape.")

    returned_agent_id = payload.get("agentId")
    agent_status = payload.get("agentStatus")
    if not isinstance(returned_agent_id, str) or not isinstance(agent_status, str):
        logger.warning("ANS identity rejected for seller=%s: missing identity fields", seller.name)
        return _live_failure(seller, "GoDaddy ANS response is missing required identity fields.")
    if returned_agent_id != ans_id:
        logger.warning("ANS identity rejected for seller=%s: agent ID mismatch", seller.name)
        return _live_failure(seller, "GoDaddy ANS agent ID does not match the seller ANS ID.")
    if agent_status != "ACTIVE":
        logger.warning("ANS identity rejected for seller=%s: agentStatus=%s", seller.name, agent_status)
        return _live_failure(seller, "GoDaddy ANS agent is not ACTIVE.")

    logger.info("ANS lookup succeeded for seller=%s ans_id=%s", seller.name, ans_id)
    result: dict[str, Any] = {
        "agent": seller.name,
        "ans_id": ans_id,
        "verified": True,
        "status": "VERIFIED",
        "source": "godaddy_ans",
    }
    if isinstance(payload.get("agentDisplayName"), str):
        result["agent_display_name"] = payload["agentDisplayName"]
    if isinstance(payload.get("agentHost"), str):
        result["agent_host"] = payload["agentHost"]
    return result


def verify_ans(seller: SellerAgent) -> dict[str, Any]:
    """Verify a seller in sandbox mode or through the GoDaddy ANS API.

    Sandbox is the default for the demo. Live mode never falls back to sandbox:
    every configuration, authentication, network, or response failure is returned
    as an unverified result.
    """
    mode = os.getenv("ANS_MODE", "sandbox").strip().lower()
    if mode == "sandbox":
        return _verify_sandbox_ans(seller)
    if mode == "live":
        return _verify_live_ans(seller)

    logger.warning("ANS identity rejected: unsupported ANS_MODE=%s", mode)
    return _live_failure(seller, "ANS_MODE must be either 'sandbox' or 'live'.")
