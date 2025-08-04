"""
HostExpert – Comprehensive host and infrastructure analysis expert.
"""

from __future__ import annotations

import json
import time
from typing import Dict, List, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.config import get_stream_writer

from app.infrastructure.security_data_repository import HostRecord
from app.llm_config import get_llm_model

KIND = "host"


class HostState(TypedDict, total=False):
    host: HostRecord
    summaries: List[Dict[str, str]]
    messages: List


def expert_node(state: HostState, config: Optional[RunnableConfig] = None) -> Dict[str, List[Dict[str, str]]]:
    """
    Comprehensive host analysis expert using real LLM analysis.
    Analyzes location, services, vulnerabilities, and threat intelligence.
    """
    start_time = time.time()

    # Get the host record from state
    host = state.get("host")
    if not host:
        return {"summaries": []}

    # Get the user's original message for context
    user_message = ""
    if state.get("messages"):
        user_message = state["messages"][-1].content if state["messages"] else ""

    # Create expert system prompt
    system_prompt = """You are a senior infrastructure security analyst conducting comprehensive \
host assessment. Analyze host record JSON data for security risks and operational concerns.

**Required Output Format** (≤200 words, markdown with emoji headers):

## 🌎 Geographic & Infrastructure Context
- Location with geopolitical considerations
- Provider/ASN and trust implications

## 🛠️ Network Services & Exposure
- Open ports/services with security implications
- Notable software versions and configurations

## 🚨 Vulnerability Assessment
[If vulnerabilities present, use table format:]
| CVE | Severity | CVSS | Description |
|-----|----------|------|-------------|

## 🕵️ Threat Intelligence
- Security labels, malware detections, risk indicators
- Known threat actor associations (if any)

## ⚠️ Priority Recommendations
1. [Most critical action required]
2. [Secondary priority items]

## 📋 Risk Summary Table
| Aspect | Status | Notes |
|--------|--------|-------|
| Patch Level | ❌/✅ | [Current state] |
| Exposure | 🚨/⚠️/✅ | [Risk level] |
| Geographic Risk | 🚨/⚠️/✅ | [Jurisdiction concerns] |

**Critical**: Report ANY extraordinary, suspicious, or unusual findings even if they \
don't fit the above sections. Focus on immediate threats, compliance gaps, attack vectors, \
and business impact. Be specific and actionable in all recommendations.

Focus on:
- Geographic location and geopolitical context
- Network infrastructure (ASN, ISP, hosting provider analysis)
- Service portfolio analysis (ports, protocols, software versions)
- Vulnerability assessment (embedded CVE data with CVSS scores)
- Threat intelligence (security labels, malware detection, risk levels)
- Infrastructure analysis (DNS hostnames, operating systems)
- Security posture and risk assessment
- Operational and compliance considerations

Provide comprehensive host analysis combining all available data points. Be precise and actionable.
Format your response with clear security insights and recommendations."""

    # Create user query combining the original message and host data
    host_data = host.model_dump() if hasattr(host, "model_dump") else host.__dict__
    user_query = f"""User Question: {user_message}

Analyze this host record comprehensively:
{json.dumps(host_data, indent=2, default=str)}

Provide a comprehensive host analysis covering security, infrastructure, and operational aspects."""

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
        confidence = min(0.95, 0.75 + (len(response.content) / 2000))  # Dynamic confidence based on response length

        content = f"🖥️ **Host Analysis**\n\n{response.content}"

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
                    "record_id": host.ip,  # Add record_id for record_done events
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
            f"🖥️ **Host Analysis** (Error: {str(e)})\n\n"
            f"📍 Host analysis for {host.ip if host else 'unknown'}: "
            "Unable to complete host analysis due to technical issues."
        )

        return {
            "summaries": [
                {
                    "kind": KIND,
                    "record_id": host.ip if host else "unknown",
                    "content": error_content,
                    "confidence": 0.3,
                    "processing_time_ms": processing_time_ms,
                }
            ]
        }
