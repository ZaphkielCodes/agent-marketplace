"""Regression tests for the sandbox marketplace's decision-making rules."""

from __future__ import annotations

import asyncio
import os
import unittest
from unittest.mock import Mock, patch

import httpx
from pydantic import ValidationError

from agents import get_seller_by_name
from ans import verify_ans
from main import RunRequest, run_marketplace
from negotiation import negotiate_with_seller


class NegotiationTests(unittest.TestCase):
    def test_counteroffer_above_budget_is_not_repriced_as_a_deal(self) -> None:
        seller = get_seller_by_name("GameHubBot")
        assert seller is not None

        result = negotiate_with_seller(seller, buyer_budget=400)

        self.assertEqual(result["buyer_offer"], 400)
        self.assertEqual(result["seller_counteroffer"], 465)
        self.assertEqual(result["final_price"], 465)
        self.assertFalse(result["within_budget"])

    def test_firm_seller_does_not_discount(self) -> None:
        seller = get_seller_by_name("DisplayWorksBot")
        assert seller is not None

        result = negotiate_with_seller(seller, buyer_budget=400)

        self.assertEqual(result["seller_counteroffer"], 330)
        self.assertTrue(result["within_budget"])


class AnsVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        seller = get_seller_by_name("TechBot")
        assert seller is not None
        self.seller = seller

    @staticmethod
    def live_environment() -> dict[str, str]:
        return {
            "ANS_MODE": "live",
            "GODADDY_PAT": "test-pat",
            "GODADDY_ANS_BASE_URL": "https://api.godaddy.com",
        }

    @staticmethod
    def response(payload: object, status_code: int = 200) -> Mock:
        response = Mock()
        response.status_code = status_code
        response.is_success = 200 <= status_code < 300
        response.json.return_value = payload
        return response

    def test_sandbox_verification_preserves_simulated_trust(self) -> None:
        unverified_seller = get_seller_by_name("BestDealBot")
        assert unverified_seller is not None

        with patch.dict(os.environ, {"ANS_MODE": "sandbox"}, clear=False):
            verified = verify_ans(self.seller)
            unverified = verify_ans(unverified_seller)

        self.assertEqual(
            verified,
            {
                "agent": "TechBot",
                "ans_id": "ans_demo_001",
                "verified": True,
                "status": "VERIFIED",
            },
        )
        self.assertFalse(unverified["verified"])
        self.assertEqual(unverified["status"], "UNVERIFIED")

    def test_live_active_matching_agent_is_verified(self) -> None:
        response = self.response(
            {
                "agentId": self.seller.ans_id,
                "lifecycle": {"status": "ACTIVE"},
                "agentHost": "seller.example",
                "ansName": "techbot.ans",
            }
        )

        with patch.dict(os.environ, self.live_environment(), clear=False), patch(
            "ans.httpx.get", return_value=response
        ) as get:
            result = verify_ans(self.seller)

        self.assertTrue(result["verified"])
        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(result["source"], "godaddy_ans")
        self.assertEqual(result["agent_host"], "seller.example")
        self.assertEqual(result["ans_name"], "techbot.ans")
        get.assert_called_once_with(
            "https://api.godaddy.com/v1/ans/registered-agents/ans_demo_001",
            headers={"Authorization": "Bearer test-pat", "Accept": "application/json"},
            timeout=10.0,
        )

    def test_live_mismatched_agent_id_is_rejected(self) -> None:
        response = self.response(
            {"agentId": "another-agent", "lifecycle": {"status": "ACTIVE"}}
        )

        with patch.dict(os.environ, self.live_environment(), clear=False), patch(
            "ans.httpx.get", return_value=response
        ):
            result = verify_ans(self.seller)

        self.assertFalse(result["verified"])
        self.assertIn("does not match", result["reason"])

    def test_live_non_active_agent_is_rejected(self) -> None:
        response = self.response(
            {"agentId": self.seller.ans_id, "lifecycle": {"status": "PENDING"}}
        )

        with patch.dict(os.environ, self.live_environment(), clear=False), patch(
            "ans.httpx.get", return_value=response
        ):
            result = verify_ans(self.seller)

        self.assertFalse(result["verified"])
        self.assertIn("not ACTIVE", result["reason"])

    def test_live_missing_pat_fails_without_request(self) -> None:
        with patch.dict(os.environ, {"ANS_MODE": "live"}, clear=True), patch(
            "ans.httpx.get"
        ) as get:
            result = verify_ans(self.seller)

        self.assertFalse(result["verified"])
        self.assertIn("GODADDY_PAT", result["reason"])
        get.assert_not_called()

    def test_live_auth_failures_are_rejected(self) -> None:
        for status_code in (401, 403):
            with self.subTest(status_code=status_code):
                with patch.dict(os.environ, self.live_environment(), clear=False), patch(
                    "ans.httpx.get", return_value=self.response({}, status_code)
                ):
                    result = verify_ans(self.seller)

                self.assertFalse(result["verified"])
                self.assertIn(str(status_code), result["reason"])

    def test_live_not_found_is_rejected(self) -> None:
        with patch.dict(os.environ, self.live_environment(), clear=False), patch(
            "ans.httpx.get", return_value=self.response({}, 404)
        ):
            result = verify_ans(self.seller)

        self.assertFalse(result["verified"])
        self.assertIn("not found", result["reason"])

    def test_live_timeout_and_network_failures_are_rejected(self) -> None:
        for error in (httpx.TimeoutException("timed out"), httpx.ConnectError("offline")):
            with self.subTest(error=error.__class__.__name__):
                with patch.dict(os.environ, self.live_environment(), clear=False), patch(
                    "ans.httpx.get", side_effect=error
                ):
                    result = verify_ans(self.seller)

                self.assertFalse(result["verified"])
                self.assertIn("request", result["reason"])

    def test_live_malformed_response_is_rejected(self) -> None:
        response = self.response({})
        response.json.side_effect = ValueError("not JSON")

        with patch.dict(os.environ, self.live_environment(), clear=False), patch(
            "ans.httpx.get", return_value=response
        ):
            result = verify_ans(self.seller)

        self.assertFalse(result["verified"])
        self.assertIn("malformed JSON", result["reason"])


class MarketplaceWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        # Keep the deterministic workflow tests offline even if a developer has
        # configured live ANS credentials in their shell.
        environment = patch.dict(os.environ, {"ANS_MODE": "sandbox"}, clear=False)
        environment.start()
        self.addCleanup(environment.stop)

    def test_unaffordable_verified_sellers_do_not_create_a_selected_deal(self) -> None:
        result = asyncio.run(run_marketplace(RunRequest(item=" PS5 ", max_price=400)))

        self.assertEqual(result["request"], {"item": "PS5", "max_price": 400})
        self.assertEqual(result["valid_offers"], [])
        self.assertIsNone(result["selected_deal"])
        self.assertEqual(len(result["rejected_agents"]), 1)

    def test_lowest_verified_affordable_offer_is_selected(self) -> None:
        result = asyncio.run(run_marketplace(RunRequest(item="PS5", max_price=490)))

        self.assertEqual(result["selected_deal"]["agent"], "GameHubBot")
        self.assertEqual(result["selected_deal"]["final_price"], 465)

    def test_request_rejects_blank_or_non_finite_price(self) -> None:
        for payload in (
            {"item": "   ", "max_price": 100},
            {"item": "PS5", "max_price": float("inf")},
            {"item": "PS5", "max_price": True},
        ):
            with self.assertRaises(ValidationError):
                RunRequest(**payload)


if __name__ == "__main__":
    unittest.main()
