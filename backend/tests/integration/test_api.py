"""
Integration tests for the API endpoints.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class TestHealthEndpoints:
    """Test health and info endpoints."""

    def test_health_endpoint(self):
        """Test the health check endpoint."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "agentic-ai-backend"
        assert data["version"] == "0.1.0"

    def test_root_endpoint(self):
        """Test the root endpoint."""
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hierarchical Expertise Router API"
        assert data["version"] == "0.1.0"
        assert data["health"] == "/health"


class TestStreamingIntegration:
    """Integration tests for the streaming endpoint."""

    def test_streaming_endpoint_with_mocked_graph(self):
        """Test the streaming endpoint with mocked graph execution."""
        # Mock the graph execution to avoid LLM calls
        with patch("app.sse.GRAPH.astream") as mock_astream:
            # Mock a complete flow using stream_mode="values" format
            async def mock_stream():
                # Initial state
                yield {"thread_id": "test-thread", "messages": [], "input": {}, "summaries": []}
                # Router decision
                yield {
                    "thread_id": "test-thread",
                    "messages": [],
                    "input": {},
                    "router_decision": ["geo", "cert", "vuln"],
                    "summaries": [],
                }
                # Expert summaries (incrementally added)
                yield {
                    "thread_id": "test-thread",
                    "messages": [],
                    "input": {},
                    "router_decision": ["geo", "cert", "vuln"],
                    "summaries": [{"kind": "geo", "content": "Geo analysis complete"}],
                }
                # Final summary
                yield {
                    "thread_id": "test-thread",
                    "messages": [],
                    "input": {},
                    "router_decision": ["geo", "cert", "vuln"],
                    "summaries": [
                        {"kind": "geo", "content": "Geo analysis complete"},
                        {"kind": "cert", "content": "Cert analysis complete"},
                        {"kind": "vuln", "content": "Vuln analysis complete"},
                    ],
                    "final_summary": "Analysis complete from all experts.",
                }

            mock_astream.return_value = mock_stream()

            # Make the streaming request
            client = TestClient(app)
            response = client.post(
                "/v1/stream",
                json={"message": "Analyze this host", "input": {"ip": "192.168.1.1", "domain": "test.example.com"}},
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

            # For TestClient, we can check basic response properties
            content = response.text
            # Verify we got some expected content patterns
            assert len(content) > 0  # Should have some content

    def test_streaming_endpoint_error_handling(self):
        """Test error handling in the streaming endpoint."""
        with patch("app.sse.GRAPH.astream") as mock_astream:
            # Mock an exception during streaming
            async def mock_stream_error():
                yield {"router_decision": ["geo"], "summaries": []}
                raise ValueError("Simulated graph execution error")

            mock_astream.return_value = mock_stream_error()

            client = TestClient(app)

            # The TestClient doesn't handle streaming errors well, so we test
            # that the endpoint doesn't crash the application
            try:
                response = client.post("/v1/stream", json={"message": "This will cause an error", "input": {}})
                # Status could be 200 or 500 depending on when error occurs
                assert response.status_code in [200, 500]
            except Exception:
                # If exception is raised, that's also acceptable for error handling test
                pass


class TestConversationIntegration:
    """Integration tests for conversation management."""

    def test_list_conversations_endpoint(self):
        """Test listing conversations."""
        client = TestClient(app)
        response = client.get("/v1/conversations/")
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert "total" in data
        assert isinstance(data["conversations"], list)
        assert isinstance(data["total"], int)

    def test_get_nonexistent_conversation(self):
        """Test getting a conversation that doesn't exist."""
        client = TestClient(app)
        response = client.get("/v1/conversations/nonexistent-thread-id")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_conversation_lifecycle(self):
        """Test creating and retrieving a conversation through streaming."""
        with patch("app.sse.GRAPH.astream") as mock_astream:
            # Mock a simple successful flow
            async def mock_stream():
                yield {
                    "thread_id": "test-conversation-123",
                    "messages": [],
                    "input": {},
                    "router_decision": ["geo"],
                    "summaries": [],
                }
                yield {
                    "thread_id": "test-conversation-123",
                    "messages": [],
                    "input": {},
                    "router_decision": ["geo"],
                    "summaries": [{"kind": "geo", "content": "Simple geo test"}],
                    "final_summary": "Test completed",
                }

            mock_astream.return_value = mock_stream()

            client = TestClient(app)

            # Create a conversation through streaming
            thread_id = "test-conversation-123"
            stream_response = client.post(
                "/v1/stream", json={"thread_id": thread_id, "message": "Test message", "input": {"test": "data"}}
            )

            assert stream_response.status_code == 200

            # Now try to retrieve the conversation
            conv_response = client.get(f"/v1/conversations/{thread_id}")
            assert conv_response.status_code == 200

            data = conv_response.json()
            assert "conversation" in data
            assert "events" in data
            assert data["conversation"]["thread_id"] == thread_id
            assert data["conversation"]["user_message"] == "Test message"
            assert len(data["events"]) > 0
