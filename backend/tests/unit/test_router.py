"""
Unit tests for router node.
"""

from app.infrastructure.security_data_repository import CertificateRecord, HostRecord
from app.langgraph.router import router_node


def test_router_split():
    """Test that router splits records correctly."""
    records = [
        HostRecord(ip="1.1.1.1"),
        CertificateRecord(fingerprint_sha256="abc123"),
    ]
    result = router_node({"records": records})

    assert set(result["router_decision"]) == {"host_fan", "cert_fan"}
    assert len(result["host_records"]) == 1
    assert len(result["cert_records"]) == 1
    assert result["host_records"][0].ip == "1.1.1.1"
    assert result["cert_records"][0].fingerprint_sha256 == "abc123"


def test_router_only_hosts():
    """Test router with only host records."""
    records = [
        HostRecord(ip="1.1.1.1"),
        HostRecord(ip="2.2.2.2"),
    ]
    result = router_node({"records": records})

    assert result["router_decision"] == ["host_fan"]
    assert len(result["host_records"]) == 2
    assert len(result["cert_records"]) == 0


def test_router_only_certs():
    """Test router with only certificate records."""
    records = [
        CertificateRecord(fingerprint_sha256="abc123"),
        CertificateRecord(fingerprint_sha256="def456"),
    ]
    result = router_node({"records": records})

    assert result["router_decision"] == ["cert_fan"]
    assert len(result["host_records"]) == 0
    assert len(result["cert_records"]) == 2


def test_router_empty_records():
    """Test router with no records."""
    result = router_node({"records": []})

    assert result["router_decision"] == []
    assert len(result["host_records"]) == 0
    assert len(result["cert_records"]) == 0
