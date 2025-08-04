"""
Builds the LangGraph workflow with map-reduce pattern:

START ➜ load_data ➜ router ➜ [host_fan, cert_fan] ➜ merge ➜ END

Map-reduce flow:
- load_data: loads Host and Certificate records from repository
- router: splits records by type into host_records and cert_records
- host_fan: uses Send to distribute each host to individual host expert analysis
- cert_fan: uses Send to distribute each cert to individual cert expert analysis
- merge: combines all individual record analyses into final summary
"""

from __future__ import annotations

from typing import Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from app.infrastructure.security_data_repository import get_dataset_repository
from app.llm_config import get_llm_model
from app.models import AgentState

from .experts.cert import expert_node as cert_expert
from .experts.host import expert_node as host_expert
from .router import router_node


def load_data_node(state: AgentState) -> Dict[str, List]:
    """
    Load Host and Certificate records from the repository for analysis.
    For demo purposes, limit to small samples for quick response.
    """
    try:
        repo = get_dataset_repository()
        hosts = repo.get_all_hosts()[:3]  # Limit to 3 hosts for demo
        certs = repo.get_all_certificates()[:3]  # Limit to 3 certs for demo

        all_records = hosts + certs

        return {
            "records": all_records,
            "stats": {"host_count": len(hosts), "cert_count": len(certs)},
        }
    except Exception as e:
        # Return empty records if loading fails
        return {
            "records": [],
            "stats": {"host_count": 0, "cert_count": 0, "error": str(e)},
        }


def fan_out_selector(state: AgentState) -> List[Send]:
    """
    Conditional edge routing function that fans out to individual expert analyses.
    Returns Send objects for each host and cert record to be processed in parallel.
    """
    sends: List[Send] = []

    # Fan out hosts to host_expert
    for host in state.get("host_records", []):
        sends.append(Send("host_expert", {"host": host, "messages": state.get("messages", [])}))

    # Fan out certs to cert_expert
    for cert in state.get("cert_records", []):
        sends.append(Send("cert_expert", {"cert": cert, "messages": state.get("messages", [])}))

    return sends


def merge_node(state: AgentState) -> Dict[str, str]:
    """
    Merge node: Generate LLM-powered executive summary from individual record analyses.
    """
    summaries = state.get("summaries", [])
    stats = state.get("stats", {})

    if not summaries:
        return {"final_summary": "No analyses completed. Check data loading and expert processing."}

    # Group summaries by type
    host_summaries = [s for s in summaries if s.get("kind") == "host"]
    cert_summaries = [s for s in summaries if s.get("kind") == "cert"]

    # Build full concatenated summary for reference (debug_full_text)
    debug_sections: List[str] = [
        "# Comprehensive Dataset Analysis\n",
        f"**Dataset Overview:** {stats.get('host_count', 0)} hosts, "
        + f"{stats.get('cert_count', 0)} certificates analyzed\n",
    ]

    # Host analyses section
    if host_summaries:
        debug_sections.extend(
            [
                "## 🖥️ Host Infrastructure Analysis\n",
                f"Analyzed {len(host_summaries)} host records:\n",
            ]
        )
        for i, summary in enumerate(host_summaries, 1):
            record_id = summary.get("record_id", "unknown")
            debug_sections.append(f"### Host {i}: {record_id}")
            debug_sections.append(summary["content"])
            debug_sections.append("")

    # Certificate analyses section
    if cert_summaries:
        debug_sections.extend(
            [
                "## 🔐 Certificate Security Analysis\n",
                f"Analyzed {len(cert_summaries)} certificate records:\n",
            ]
        )
        for i, summary in enumerate(cert_summaries, 1):
            record_id = summary.get("record_id", "unknown")
            fingerprint = record_id
            debug_sections.append(f"### Certificate {i}: {fingerprint}")
            debug_sections.append(summary["content"])
            debug_sections.append("")

    debug_full_text = "\n".join(debug_sections)

    # Build terse bullet points for LLM context
    host_bullets = []
    for i, summary in enumerate(host_summaries, 1):
        record_id = summary.get("record_id", "unknown")
        content = summary["content"][:200000] + "..." if len(summary["content"]) > 200000 else summary["content"]
        host_bullets.append(f"• Host {record_id}: {content}")

    cert_bullets = []
    for i, summary in enumerate(cert_summaries, 1):
        record_id = summary.get("record_id", "unknown")
        fingerprint = record_id
        content = summary["content"][:200000] + "..." if len(summary["content"]) > 200000 else summary["content"]
        cert_bullets.append(f"• Cert {fingerprint}: {content}")

    # Generate LLM executive summary
    try:
        system_prompt = """You are a CISO presenting security findings to executive leadership. \
Synthesize expert analyses into business-focused insights.

**Audience**: C-level executives needing actionable security decisions
**Format**: ≤250 words, four required sections with business impact focus

## 🚨 Critical Risks
[Business impact focus - what could go wrong and cost/reputation implications]

## 📊 Security Patterns
[Cross-cutting themes, common vulnerabilities, infrastructure concentrations]

## ⚡ Quick Wins
[Low-effort, high-impact improvements with estimated effort/cost]

## 🛡️ Strategic Recommendations
[Investment priorities, compliance considerations, long-term security posture]

**Guidelines**: Quantify risks where possible, avoid technical jargon, focus on business \
impact, include rough effort estimates, highlight regulatory/compliance implications. \
Reference specific findings by record ID when relevant. Report any extraordinary or \
suspicious patterns that require immediate executive attention."""

        separator = "\n\n---\n\n"  # Use a clear separator for readability
        context_content = f"""Dataset Overview: {stats.get('host_count', 0)} hosts, \
{stats.get('cert_count', 0)} certificates analyzed

---

HOST FINDINGS:

---

{separator.join(host_bullets)}

---

CERTIFICATE FINDINGS:

---

{separator.join(cert_bullets)}

---

Write a concise executive summary focusing on the most critical security insights and patterns across all records."""

        llm = get_llm_model()  # Use default model (gpt-4.1)

        # Limit context length to avoid API errors
        # Conservative estimate: 1 token ≈ 3-4 chars, so 1M tokens ≈ 3-4M chars
        # Using 800K chars as safe limit for 1M token models (leaving headroom for system prompt)
        max_context_chars = 800000
        if len(context_content) > max_context_chars:
            context_content = context_content[:max_context_chars] + "\n\n[Content truncated to fit 1M token limit]"

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=context_content)]

        response = llm.invoke(messages)
        executive_summary = f"# 📊 Executive Summary\n\n{response.content}"

    except Exception as e:
        # Fallback if LLM fails
        executive_summary = f"""# 📊 Executive Summary

Dataset analysis completed successfully:
- **{len(host_summaries)}** host infrastructure assessments
- **{len(cert_summaries)}** certificate security evaluations
- **{len(summaries)}** total individual record analyses completed

Review the detailed findings above for specific security insights and recommendations.

*Note: LLM summary generation failed: {str(e)}*"""

    return {
        "final_summary": executive_summary,
        "debug_full_text": debug_full_text,  # Keep for debugging/reference
    }


def build_graph():
    builder: StateGraph[AgentState] = StateGraph(AgentState)

    # ---- Nodes ------------------------------------------------------------- #
    builder.add_node("load_data", load_data_node)
    builder.add_node("router", router_node)
    builder.add_node("host_expert", host_expert)
    builder.add_node("cert_expert", cert_expert)
    builder.add_node("merge", merge_node)

    # ---- Edges ------------------------------------------------------------- #
    builder.add_edge(START, "load_data")
    builder.add_edge("load_data", "router")

    # Conditional fan-out - Send objects are returned by the routing function
    builder.add_conditional_edges("router", fan_out_selector)

    # Expert nodes connect to merge
    builder.add_edge("host_expert", "merge")
    builder.add_edge("cert_expert", "merge")
    builder.add_edge("merge", END)

    return builder.compile()


# Singleton graph instance – imported by FastAPI route
GRAPH = build_graph()
