"""
Integration tests for the streaming endpoint with real LLM calls.
"""

from .utils import collect_sse


class TestStreamEndpoint:
    """Integration tests for /v1/stream endpoint."""

    def test_stream_end_to_end(self, client):
        """Test complete streaming flow with real LLM calls."""
        resp = client.post("/v1/stream", json={"message": "analyze dataset"})

        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

        events = collect_sse(resp.text)

        # Check event types we expect
        router_decision = [e for e in events if e.get("event") == "router_decision"]
        record_done = [e for e in events if e.get("event") == "record_done"]
        final_summary = [e for e in events if e.get("event") == "final_summary"]

        # Assertions based on load_data_node limits (3 hosts + 3 certs)
        assert len(router_decision) == 1, f"Expected 1 router_decision, got {len(router_decision)}"
        assert len(record_done) == 6, f"Expected 6 record_done events, got {len(record_done)}"
        assert len(final_summary) == 1, f"Expected 1 final_summary, got {len(final_summary)}"

        # Check router selected both experts
        router_payload = router_decision[0]["payload"]
        assert "host_fan" in router_payload.get("selected_experts", [])
        assert "cert_fan" in router_payload.get("selected_experts", [])

        # Check record_done events have the right structure
        host_records = [r for r in record_done if r.get("payload", {}).get("kind") == "host"]
        cert_records = [r for r in record_done if r.get("payload", {}).get("kind") == "cert"]

        assert len(host_records) == 3, f"Expected 3 host records, got {len(host_records)}"
        assert len(cert_records) == 3, f"Expected 3 cert records, got {len(cert_records)}"

        # Verify structure of record_done events
        for record in record_done:
            payload = record.get("payload", {})
            assert "kind" in payload
            assert "id" in payload
            assert "summary" in payload
            assert len(payload["summary"]) > 0

        # Verify final summary exists and has content
        final = final_summary[0]
        assert "summary" in final["payload"]
        assert len(final["payload"]["summary"]) > 100  # Should be substantial
        assert final["payload"].get("expert_count") == 6  # 6 individual record analyses

    def test_stream_with_custom_message(self, client):
        """Test streaming with custom analysis message."""
        resp = client.post(
            "/v1/stream", json={"message": "Provide security analysis focusing on vulnerabilities", "input": {}}
        )

        assert resp.status_code == 200
        events = collect_sse(resp.text)

        # Should still get the same structure
        final_events = [e for e in events if e.get("event") == "final_summary"]
        assert len(final_events) == 1

        # Final summary should contain analysis content
        final_summary = final_events[0]["payload"]["summary"]
        assert "analysis" in final_summary.lower() or "security" in final_summary.lower()

    def test_stream_error_handling(self, client):
        """Test streaming endpoint error handling."""
        # Test with empty message
        resp = client.post("/v1/stream", json={"message": "", "input": {}})

        # Should handle gracefully (either process empty message or return error)
        assert resp.status_code in [200, 422]  # 422 for validation error
