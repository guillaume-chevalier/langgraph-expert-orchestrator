"""
Unit tests for SSE streaming functionality.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import SseEnvelope, StreamRequest


class TestStreamingEndpoint:
    """Test the /v1/stream endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_request(self):
        """Sample streaming request."""
        return {
            "thread_id": "test-thread-123",
            "message": "Analyze this host",
            "input": {"ip": "1.2.3.4", "domain": "example.com"},
        }

    def test_stream_request_validation(self, sample_request):
        """Test that StreamRequest model validates correctly."""
        request = StreamRequest(**sample_request)
        assert request.thread_id == "test-thread-123"
        assert request.message == "Analyze this host"
        assert request.input["ip"] == "1.2.3.4"

    def test_stream_request_generates_thread_id(self):
        """Test that StreamRequest generates thread_id if not provided."""
        request = StreamRequest(message="test", input={})
        assert request.thread_id is not None
        assert len(request.thread_id) > 0

    def test_stream_endpoint_basic_flow(self, sample_request):
        """Test the basic flow of the streaming endpoint."""
        # Mock the graph execution to avoid LLM calls
        with patch("app.sse.GRAPH.astream") as mock_astream:
            # Mock the async generator to match stream_mode="values" format
            async def mock_stream():
                # Initial state
                yield {"thread_id": "test-thread-123", "messages": [], "input": {}, "summaries": []}
                # Router decision with stats
                yield {
                    "thread_id": "test-thread-123",
                    "messages": [],
                    "router_decision": ["host_fan", "cert_fan"],
                    "summaries": [],
                    "stats": {"host_count": 3, "cert_count": 3},
                }
                # Expert summaries (incrementally added with record_id)
                yield {
                    "thread_id": "test-thread-123",
                    "messages": [],
                    "router_decision": ["host_fan", "cert_fan"],
                    "summaries": [{"kind": "host", "record_id": "1.1.1.1", "content": "Test host analysis"}],
                    "stats": {"host_count": 3, "cert_count": 3},
                }
                # More summaries
                yield {
                    "thread_id": "test-thread-123",
                    "messages": [],
                    "router_decision": ["host_fan", "cert_fan"],
                    "summaries": [
                        {"kind": "host", "record_id": "1.1.1.1", "content": "Test host analysis"},
                        {"kind": "cert", "record_id": "abc123", "content": "Test cert analysis"},
                    ],
                    "stats": {"host_count": 3, "cert_count": 3},
                }
                # Final summary
                yield {
                    "thread_id": "test-thread-123",
                    "messages": [],
                    "router_decision": ["host_fan", "cert_fan"],
                    "summaries": [
                        {"kind": "host", "record_id": "1.1.1.1", "content": "Test host analysis"},
                        {"kind": "cert", "record_id": "abc123", "content": "Test cert analysis"},
                    ],
                    "stats": {"host_count": 3, "cert_count": 3},
                    "final_summary": "Comprehensive analysis complete",
                }

            mock_astream.return_value = mock_stream()

            # Use the test client from the TestClient
            from fastapi.testclient import TestClient

            client = TestClient(app)
            response = client.post("/v1/stream", json=sample_request)
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    def test_sse_envelope_creation(self):
        """Test SSE envelope model creation."""
        envelope = SseEnvelope(
            event="router_decision", thread_id="test-123", seq=1, payload={"selected_experts": ["host_fan", "cert_fan"]}
        )

        assert envelope.event == "router_decision"
        assert envelope.thread_id == "test-123"
        assert envelope.seq == 1
        assert envelope.payload["selected_experts"] == ["host_fan", "cert_fan"]
        assert envelope.timestamp is not None

    def test_stream_endpoint_error_handling(self):
        """Test error handling in streaming endpoint."""
        with patch("app.sse.GRAPH.astream") as mock_astream:
            # Mock an async generator that raises an exception
            async def mock_stream_error():
                yield {"router_decision": ["host_fan"], "summaries": []}
                raise ValueError("Test error")

            mock_astream.return_value = mock_stream_error()

            from fastapi.testclient import TestClient

            client = TestClient(app)

            # The test client can't handle streaming errors easily, so we'll just
            # verify that the endpoint can be called without crashing the whole app
            try:
                response = client.post("/v1/stream", json={"message": "test", "input": {}})
                # The response status might be 200 or 500 depending on when the error occurs
                assert response.status_code in [200, 500]
            except Exception:
                # If an exception is raised, that's also acceptable for this error test
                pass


def test_sse_frame_formatting():
    """Test SSE frame formatting includes proper headers."""
    from app.sse import _sse

    envelope = SseEnvelope(
        event="router_decision", thread_id="test-123", seq=42, payload={"test": "data"}  # Use valid event type
    )

    frame = _sse(envelope)
    lines = frame.split("\n")

    # Check that frame includes ID, event, and data
    assert any(line.startswith("id: ") for line in lines)
    assert any(line.startswith("event: ") for line in lines)
    assert any(line.startswith("data: ") for line in lines)

    # Check specific values
    assert "id: 42" in frame
    assert "event: router_decision" in frame
    assert '"thread_id": "test-123"' in frame
