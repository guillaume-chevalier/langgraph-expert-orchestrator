"""
CertExpert – Real LLM implementation for certificate and cryptographic analysis.
"""

from __future__ import annotations

import json
import time
from typing import Dict, List, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.config import get_stream_writer

from app.infrastructure.security_data_repository import CertificateRecord
from app.llm_config import get_llm_model

KIND = "cert"


class CertState(TypedDict, total=False):
    cert: CertificateRecord
    summaries: List[Dict[str, str]]
    messages: List


def expert_node(state: CertState, config: Optional[RunnableConfig] = None) -> Dict[str, List[Dict[str, str]]]:
    """
    Certificate and cryptographic analysis expert using real LLM analysis.
    """
    start_time = time.time()

    # Get the certificate record from state
    cert = state.get("cert")
    if not cert:
        return {"summaries": []}

    # Get the user's original message for context
    user_message = ""
    if state.get("messages"):
        user_message = state["messages"][-1].content if state["messages"] else ""

    # Create expert system prompt
    system_prompt = """You are a senior PKI and cryptographic security specialist analyzing \
certificate data. Review certificate JSON for security, compliance, and trust issues.

**Required Output Format** (≤200 words, markdown with emoji headers):

## 🔗 Certificate Chain & Trust
- Issuer with validation level and trust status
- Browser compatibility and trust store acceptance

## 🔒 Cryptographic Strength
- Algorithm/key size assessment vs. current standards
- Cipher suite and hash function security posture

## 📅 Validity & Lifecycle Management
- Current status (active/expired/revoked)
- Renewal timeline and automation recommendations

## 🛡️ Compliance & Standards
- CT logging status, OCSP/CRL availability
- Linting results and baseline requirement violations

## ⚠️ Security Recommendations
1. [Most critical remediation needed]
2. [Compliance improvements required]

## 📋 Security Summary Table
| Aspect | Status | Notes |
|--------|--------|-------|
| Browser Trust | ❌/✅ | [Trust store status] |
| Crypto Strength | 🚨/⚠️/✅ | [Algorithm assessment] |
| Compliance | ❌/⚠️/✅ | [Standards adherence] |
| Risk Level | 🚨/⚠️/✅ | [Overall assessment] |

**Critical**: Report ANY extraordinary, suspicious, or unusual findings even if they \
don't fit the above sections. Focus on trust failures, crypto weaknesses, compliance \
gaps, and operational risks. Be specific and actionable in all recommendations.

Focus on:
- SSL/TLS certificate validation and chain analysis
- Certificate authority (CA) trust and reputation
- Cryptographic algorithm strength and compliance
- Key exchange mechanisms and cipher suites
- Certificate transparency and OCSP analysis
- Expiration dates and renewal processes
- Certificate pinning and HSTS implementation
- PKI best practices and security recommendations
- Common certificate vulnerabilities and misconfigurations

Provide detailed certificate security analysis and actionable recommendations. Be precise and technical.
Format your response with clear certificate insights and security findings."""

    # Create user query combining the original message and certificate data
    cert_data = cert.model_dump() if hasattr(cert, "model_dump") else cert.__dict__
    user_query = f"""User Question: {user_message}

Analyze this certificate record from a cryptographic security perspective:
{json.dumps(cert_data, indent=2, default=str)}

Provide a comprehensive certificate and cryptographic analysis."""

    try:
        # Get LLM instance
        llm = get_llm_model()

        # Create messages
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_query)]

        # Call LLM
        response = llm.invoke(messages)
        end_time = time.time()

        # Calculate metrics
        processing_time_ms = int((end_time - start_time) * 1000)
        confidence = min(0.98, 0.80 + (len(response.content) / 2500))  # Dynamic confidence based on response length

        content = f"🔐 **Certificate Analysis**\n\n{response.content}"

        # Send incremental chunk for UI responsiveness
        try:
            writer = get_stream_writer()
            writer({"type": "expert_chunk", "kind": KIND, "content": content})
        except RuntimeError:
            # get_stream_writer() not available outside of streaming context
            pass

        return {
            "summaries": [
                {
                    "kind": KIND,
                    "record_id": cert.fingerprint_sha256,  # Add record_id for record_done events
                    "content": content,
                    "confidence": confidence,
                    "processing_time_ms": processing_time_ms,
                }
            ]
        }

    except Exception as e:
        end_time = time.time()
        processing_time_ms = int((end_time - start_time) * 1000)

        # Fallback content in case of LLM failure
        error_content = (
            f"🔐 **Certificate Analysis** (Error: {str(e)})\n\n"
            f"🔐 Certificate {cert.fingerprint_sha256 if cert else 'unknown'}: "
            "Unable to complete certificate analysis due to technical issues."
        )

        return {
            "summaries": [
                {
                    "kind": KIND,
                    "record_id": cert.fingerprint_sha256 if cert else "unknown",
                    "content": error_content,
                    "confidence": 0.3,
                    "processing_time_ms": processing_time_ms,
                }
            ]
        }
