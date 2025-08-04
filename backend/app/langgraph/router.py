"""
Router node: splits records by type and decides which expert fan-out nodes to invoke.
"""

from __future__ import annotations

from typing import Any, Dict

from app.infrastructure.security_data_repository import CertificateRecord, HostRecord
from app.models import AgentState


def router_node(state: AgentState) -> Dict[str, Any]:
    """
    Split records by type and decide which fan-out nodes to invoke.

    Returns:
        Dictionary with router_decision and split record lists
    """
    records = state.get("records", [])

    # Split records by type using isinstance checks
    host_records = [record for record in records if isinstance(record, HostRecord)]
    cert_records = [record for record in records if isinstance(record, CertificateRecord)]

    # Decide which fan-out wrapper nodes to invoke based on available records
    decision = []
    if host_records:
        decision.append("host_fan")
    if cert_records:
        decision.append("cert_fan")

    return {
        "router_decision": decision,
        "host_records": host_records,
        "cert_records": cert_records,
    }
