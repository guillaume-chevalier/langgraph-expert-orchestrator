"""
Unit tests for expert nodes.
"""

from unittest.mock import Mock, patch

from app.infrastructure.security_data_repository import CertificateRecord, HostRecord
from app.langgraph.experts.cert import KIND as CERT_KIND
from app.langgraph.experts.cert import expert_node as cert_expert
from app.langgraph.experts.host import KIND as HOST_KIND
from app.langgraph.experts.host import expert_node as host_expert


# Mock RunnableConfig for tests
def create_mock_config():
    """Create a mock RunnableConfig for testing."""
    return {"configurable": {"thread_id": "test-thread"}}


class TestHostExpert:
    """Test the host expert node."""

    @patch("app.langgraph.experts.host.get_stream_writer")
    def test_host_expert_basic_analysis(self, mock_stream_writer):
        """Test basic host analysis functionality."""
        mock_writer = Mock()
        mock_stream_writer.return_value = mock_writer

        state = {"host": HostRecord(ip="8.8.8.8"), "summaries": []}

        result = host_expert(state)

        assert "summaries" in result
        assert len(result["summaries"]) == 1
        assert result["summaries"][0]["kind"] == HOST_KIND
        assert result["summaries"][0]["record_id"] == "8.8.8.8"
        assert "host" in result["summaries"][0]["content"].lower()

        # Verify stream writer was called
        mock_writer.assert_called_once()

    @patch("app.langgraph.experts.host.get_stream_writer")
    def test_host_expert_no_host(self, mock_stream_writer):
        """Test host expert with missing host."""
        mock_writer = Mock()
        mock_stream_writer.return_value = mock_writer

        state = {"summaries": []}

        result = host_expert(state, create_mock_config())

        assert "summaries" in result
        assert len(result["summaries"]) == 0  # Should return empty if no host

    def test_host_expert_kind_constant(self):
        """Test that host expert KIND is correct."""
        assert HOST_KIND == "host"


class TestCertExpert:
    """Test the cert expert node."""

    @patch("app.langgraph.experts.cert.get_stream_writer")
    def test_cert_expert_basic_analysis(self, mock_stream_writer):
        """Test basic cert analysis functionality."""
        mock_writer = Mock()
        mock_stream_writer.return_value = mock_writer

        state = {"cert": CertificateRecord(fingerprint_sha256="abc123"), "summaries": []}

        result = cert_expert(state)

        assert "summaries" in result
        assert len(result["summaries"]) == 1
        assert result["summaries"][0]["kind"] == CERT_KIND
        assert result["summaries"][0]["record_id"] == "abc123"
        assert "certificate" in result["summaries"][0]["content"].lower()

    @patch("app.langgraph.experts.cert.get_stream_writer")
    def test_cert_expert_no_cert(self, mock_stream_writer):
        """Test cert expert with missing certificate."""
        mock_writer = Mock()
        mock_stream_writer.return_value = mock_writer

        state = {"summaries": []}

        result = cert_expert(state, create_mock_config())

        assert "summaries" in result
        assert len(result["summaries"]) == 0  # Should return empty if no cert

    def test_cert_expert_kind_constant(self):
        """Test that cert expert KIND is correct."""
        assert CERT_KIND == "cert"


class TestExpertIntegration:
    """Test expert integration scenarios."""

    def test_all_experts_return_consistent_format(self):
        """Test that all experts return the same format."""
        host_state = {"host": HostRecord(ip="1.2.3.4"), "summaries": []}
        cert_state = {"cert": CertificateRecord(fingerprint_sha256="abc123"), "summaries": []}

        experts = [host_expert, cert_expert]
        kinds = [HOST_KIND, CERT_KIND]
        states = [host_state, cert_state]

        with (
            patch("app.langgraph.experts.host.get_stream_writer"),
            patch("app.langgraph.experts.cert.get_stream_writer"),
        ):

            for expert, expected_kind, state in zip(experts, kinds, states):
                result = expert(state, create_mock_config())

                # Check structure
                assert "summaries" in result
                assert len(result["summaries"]) == 1

                # Check content
                summary = result["summaries"][0]
                assert "kind" in summary
                assert "content" in summary
                assert "record_id" in summary
                assert summary["kind"] == expected_kind
                assert len(summary["content"]) > 0
