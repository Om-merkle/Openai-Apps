"""Regression tests for the public MCP endpoint and transport security."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app


INITIALIZE_REQUEST = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "weather-info-tests", "version": "1.0"},
    },
}

MCP_HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
    "MCP-Protocol-Version": "2025-06-18",
}


class TransportSecuritySettingsTests(unittest.TestCase):
    """Verify that public transport rules are derived from application settings."""

    def test_public_url_adds_exact_hostname_and_origin(self) -> None:
        settings = Settings(
            connect_base_url="https://weather-info.onrender.com",
            allowed_origins=["https://chatgpt.com"],
        )

        self.assertIn("weather-info.onrender.com", settings.mcp_allowed_hosts)
        self.assertIn("weather-info.onrender.com:*", settings.mcp_allowed_hosts)
        self.assertIn("https://weather-info.onrender.com", settings.mcp_allowed_origins)
        self.assertIn("https://chatgpt.com", settings.mcp_allowed_origins)

    def test_loopback_hosts_remain_available(self) -> None:
        settings = Settings(connect_base_url="")

        self.assertIn("127.0.0.1:*", settings.mcp_allowed_hosts)
        self.assertIn("localhost:*", settings.mcp_allowed_hosts)
        self.assertIn("[::1]:*", settings.mcp_allowed_hosts)


class MCPTransportIntegrationTests(unittest.TestCase):
    """Exercise the canonical endpoint through the complete ASGI stack."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client_context = TestClient(
            app,
            base_url="http://127.0.0.1:8000",
            follow_redirects=False,
        )
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_context.__exit__(None, None, None)

    def test_canonical_mcp_path_does_not_redirect(self) -> None:
        response = self.client.post("/mcp", json=INITIALIZE_REQUEST, headers=MCP_HEADERS)

        self.assertEqual(response.status_code, 200, response.text)
        self.assertNotIn("location", response.headers)
        self.assertEqual(response.json()["result"]["serverInfo"]["name"], "Weather Info")

    def test_configured_chatgpt_origin_is_allowed(self) -> None:
        response = self.client.post(
            "/mcp",
            json=INITIALIZE_REQUEST,
            headers={**MCP_HEADERS, "Origin": "https://chatgpt.com"},
        )

        self.assertEqual(response.status_code, 200, response.text)

    def test_unknown_host_is_rejected(self) -> None:
        response = self.client.post(
            "/mcp",
            json=INITIALIZE_REQUEST,
            headers={**MCP_HEADERS, "Host": "attacker.example"},
        )

        self.assertEqual(response.status_code, 421, response.text)

    def test_unknown_origin_is_rejected(self) -> None:
        response = self.client.post(
            "/mcp",
            json=INITIALIZE_REQUEST,
            headers={**MCP_HEADERS, "Origin": "https://attacker.example"},
        )

        self.assertEqual(response.status_code, 403, response.text)


if __name__ == "__main__":
    unittest.main()
