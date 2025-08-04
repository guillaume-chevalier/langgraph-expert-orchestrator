"""
Integration tests using real OpenAI API calls with hardcoded test data.
These tests will use actual gpt-4.1 calls for realistic end-to-end testing.
"""

import os

import pytest
from fastapi.testclient import TestClient

from app.main import app

# Skip these tests if no OpenAI API key is provided or if we're in CI
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "test-key-for-testing",
    reason="Real OpenAI API key required for integration tests",
)

# Hardcoded test data representing realistic security analysis scenarios
TEST_HOST_DATA = {
    "suspicious_host": {
        "ip": "185.220.100.240",
        "domain": "suspicious-domain.onion",
        "os": "ubuntu-20.04",
        "ports": [22, 80, 443, 9050],
        "services": ["ssh", "http", "https", "tor"],
        "country": "Romania",
        "asn": "AS13335",
    },
    "corporate_host": {
        "ip": "8.8.8.8",
        "domain": "dns.google",
        "os": "linux",
        "ports": [53, 443, 853],
        "services": ["dns", "https", "dns-over-tls"],
        "country": "United States",
        "asn": "AS15169",
        "organization": "Google LLC",
    },
    "vulnerable_host": {
        "ip": "192.168.1.100",
        "domain": "legacy-server.internal",
        "os": "windows-server-2008",
        "ports": [135, 139, 445, 3389, 5985],
        "services": ["rpc", "netbios", "smb", "rdp", "winrm"],
        "software": ["iis/7.5", "mysql/5.1.73", "php/5.3.29"],
        "last_updated": "2019-03-15",
    },
}

TEST_CERTIFICATE_DATA = {
    "expired_cert": {
        "domain": "expired-ssl.badssl.com",
        "ip": "104.154.89.105",
        "port": 443,
        "protocol": "https",
        "issuer": "COMODO CA Limited",
        "subject": "expired-ssl.badssl.com",
        "valid_from": "2015-04-09",
        "valid_to": "2015-04-12",
        "signature_algorithm": "SHA256-RSA",
        "key_size": 2048,
    },
    "valid_cert": {
        "domain": "google.com",
        "ip": "142.250.191.14",
        "port": 443,
        "protocol": "https",
        "issuer": "Google Trust Services",
        "subject": "*.google.com",
        "signature_algorithm": "SHA256-RSA",
        "key_size": 2048,
    },
}


class TestRealLLMIntegration:
    """Integration tests using real LLM calls."""

    def test_end_to_end_suspicious_host_analysis(self):
        """Test complete analysis of a suspicious host using real LLM."""
        client = TestClient(app)

        # Use suspicious host data
        test_data = TEST_HOST_DATA["suspicious_host"]

        response = client.post(
            "/v1/stream",
            json={
                "message": "Analyze this host for security threats and suspicious activity. "
                "Provide detailed assessment.",
                "input": test_data,
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        # Parse SSE events from response
        print("Response status:", response.status_code)
        print("Response headers:", dict(response.headers))
        print("Response text length:", len(response.text))
        print("Response text (first 500 chars):", repr(response.text[:500]))

        events = self._parse_sse_events(response.text)
        print("Parsed events:", len(events))

        # Verify we got the expected event types
        event_types = [event["event"] for event in events]
        assert "router_decision" in event_types
        assert "record_done" in event_types
        assert "final_summary" in event_types

        # Verify experts were selected and completed
        router_events = [e for e in events if e["event"] == "router_decision"]
        assert len(router_events) > 0

        record_done_events = [e for e in events if e["event"] == "record_done"]
        assert len(record_done_events) >= 2  # Should have multiple record analyses

        # Verify final summary exists and has content
        final_events = [e for e in events if e["event"] == "final_summary"]
        assert len(final_events) == 1
        final_summary = final_events[0]["payload"]["summary"]
        assert len(final_summary) > 100  # Should be substantial
        assert "suspicious" in final_summary.lower() or "threat" in final_summary.lower()

    def test_corporate_host_analysis(self):
        """Test analysis of a legitimate corporate host."""
        client = TestClient(app)

        test_data = TEST_HOST_DATA["corporate_host"]

        response = client.post(
            "/v1/stream",
            json={
                "message": "Perform security assessment of this Google DNS server. "
                "Focus on legitimacy and security posture.",
                "input": test_data,
            },
        )

        assert response.status_code == 200

        events = self._parse_sse_events(response.text)

        # Should complete successfully
        assert any(e["event"] == "final_summary" for e in events)

        # Find final summary
        final_events = [e for e in events if e["event"] == "final_summary"]
        final_summary = final_events[0]["payload"]["summary"]

        # Should mention Google/legitimate
        assert "google" in final_summary.lower() or "legitimate" in final_summary.lower()

    def test_vulnerable_legacy_system(self):
        """Test analysis of an outdated, vulnerable system."""
        client = TestClient(app)

        test_data = TEST_HOST_DATA["vulnerable_host"]

        response = client.post(
            "/v1/stream",
            json={
                "message": "Assess vulnerabilities in this legacy Windows server. Identify critical security risks.",
                "input": test_data,
            },
        )

        assert response.status_code == 200

        events = self._parse_sse_events(response.text)

        # Should identify vulnerability concerns
        final_events = [e for e in events if e["event"] == "final_summary"]
        final_summary = final_events[0]["payload"]["summary"]

        # Should mention vulnerabilities/risks
        vulnerability_terms = ["vulnerable", "risk", "outdated", "legacy", "critical", "patch"]
        assert any(term in final_summary.lower() for term in vulnerability_terms)

    def test_certificate_analysis(self):
        """Test certificate-specific analysis."""
        client = TestClient(app)

        response = client.post(
            "/v1/stream",
            json={"message": "Analyze SSL certificates for security issues and validity."},
        )

        assert response.status_code == 200

        events = self._parse_sse_events(response.text)

        # Should have certificate expert analysis
        record_events = [e for e in events if e["event"] == "record_done"]
        cert_record_events = [e for e in record_events if e["payload"]["kind"] == "cert"]
        assert len(cert_record_events) > 0

        # Should have certificate analysis content
        cert_summary = cert_record_events[0]["payload"]["summary"]
        assert len(cert_summary) > 50  # Should have substantial analysis content
        assert "certificate" in cert_summary.lower() or "cert" in cert_summary.lower()

    def test_geographic_analysis(self):
        """Test geographic/network analysis focus."""
        client = TestClient(app)

        # Create data focused on geographic analysis
        geo_focused_data = {
            "ip": "185.220.100.240",  # Romanian IP
            "country": "Romania",
            "city": "Bucharest",
            "asn": "AS13335",
            "organization": "Unknown Provider",
            "latitude": 44.4268,
            "longitude": 26.1025,
        }

        response = client.post(
            "/v1/stream",
            json={
                "message": "Analyze the geographic and network origin of this IP address. Assess location-based risks.",
                "input": geo_focused_data,
            },
        )

        assert response.status_code == 200

        events = self._parse_sse_events(response.text)

        # Should have host analysis (includes geographic data)
        record_events = [e for e in events if e["event"] == "record_done"]
        host_record_events = [e for e in record_events if e["payload"]["kind"] == "host"]
        assert len(host_record_events) > 0

        # Should mention Romania or geographic elements
        geo_summary = host_record_events[0]["payload"]["summary"]
        assert (
            "romania" in geo_summary.lower()
            or "bucharest" in geo_summary.lower()
            or "geographic" in geo_summary.lower()
        )

    def _parse_sse_events(self, sse_text: str) -> list:
        """Parse SSE event stream into structured events."""
        import json

        events = []
        lines = sse_text.strip().split("\n")

        current_event = {}
        for line in lines:
            line = line.strip()
            if line.startswith("id:"):
                current_event["id"] = line[3:].strip()
            elif line.startswith("event:"):
                current_event["event"] = line[6:].strip()
            elif line.startswith("data:"):
                try:
                    data = json.loads(line[5:].strip())
                    current_event.update(data)
                    events.append(current_event.copy())
                    current_event = {}
                except json.JSONDecodeError:
                    continue

        return events
