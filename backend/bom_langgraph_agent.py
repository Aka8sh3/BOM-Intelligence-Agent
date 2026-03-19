"""
BOM LangGraph Agent
===================
Five-node state machine that processes PCN text end-to-end:

    parse_pcn  →  query_kg  →  find_alternates  →  assess_risk  →  generate_report

Works in rule-based mode (no API key needed).
When you add ANTHROPIC_API_KEY to a .env file it uses Claude for smarter parsing.
"""

from __future__ import annotations

import os
import re
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, END

# Local imports
from bom_kg_schema import (
    BOMKnowledgeGraph, build_demo_graph,
    Severity, ChangeType, Lifecycle,
)

# ── Optional LLM setup ──────────────────────────────────────────────────────

_llm = None

def _get_llm():
    """Try to create an LLM client.  Returns None if no key is available."""
    global _llm
    if _llm is not None:
        return _llm
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key:
            from langchain_anthropic import ChatAnthropic
            _llm = ChatAnthropic(model="claude-sonnet-4-20250514", api_key=api_key)
            return _llm
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if api_key:
            from langchain_openai import ChatOpenAI
            _llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)
            return _llm
    except Exception:
        pass
    return None


# ── State schema ─────────────────────────────────────────────────────────────

class AgentState(TypedDict, total=False):
    # Inputs
    pcn_text: str
    kg: Any  # BOMKnowledgeGraph reference (not serialised)

    # Step outputs
    parsed_pcn: dict
    affected_assemblies: list
    alternates: dict          # {part_number: [alternates]}
    risk_assessment: dict
    report: dict

    # Meta
    errors: list
    status: str


# ── Node functions ───────────────────────────────────────────────────────────

def parse_pcn(state: AgentState) -> AgentState:
    """Extract component part numbers, change type, and dates from PCN text."""
    pcn_text = state.get("pcn_text", "")
    errors = list(state.get("errors", []))

    # Try LLM first
    llm = _get_llm()
    if llm:
        try:
            prompt = (
                "Extract the following from this PCN notice as JSON:\n"
                "- affected_parts: list of component part numbers\n"
                "- change_type: one of Obsolescence|Process Change|Material Change|Package Change|Site Change|Specification Change\n"
                "- effective_date: date string or empty\n"
                "- last_buy_date: date string or empty\n"
                "- summary: one-line summary\n\n"
                f"PCN Text:\n{pcn_text}\n\n"
                "Return ONLY valid JSON, no markdown."
            )
            resp = llm.invoke(prompt)
            content = resp.content if hasattr(resp, "content") else str(resp)
            parsed = json.loads(content)
            return {**state, "parsed_pcn": parsed, "status": "pcn_parsed"}
        except Exception as e:
            errors.append(f"LLM parse failed, falling back to rule-based: {e}")

    # Rule-based fallback
    parsed: Dict[str, Any] = {
        "affected_parts": [],
        "change_type": "Obsolescence",
        "effective_date": "",
        "last_buy_date": "",
        "summary": "",
    }

    # Extract part numbers — electronics part numbers typically contain
    # a mix of letters and digits, with optional hyphens/dots
    # Exclude pure date patterns (YYYY-MM-DD) and PCN reference IDs
    pn_candidates = re.findall(
        r'\b([A-Z]{1,5}[0-9][A-Z0-9\-\.]{4,})\b',
        pcn_text.upper()
    )
    # Filter out date-like patterns and PCN reference IDs
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    pcn_ref_pattern = re.compile(r'^PCN-\d{4}-\d+$', re.IGNORECASE)
    # Deduplicate while preserving order
    seen = set()
    parts = []
    for p in pn_candidates:
        if p in seen:
            continue
        if date_pattern.match(p) or pcn_ref_pattern.match(p):
            continue
        seen.add(p)
        parts.append(p)
    parsed["affected_parts"] = parts

    # Change type
    text_lower = pcn_text.lower()
    if any(w in text_lower for w in ["obsolete", "obsolescence", "end of life", "eol", "discontinued"]):
        parsed["change_type"] = "Obsolescence"
    elif "process" in text_lower:
        parsed["change_type"] = "Process Change"
    elif "material" in text_lower:
        parsed["change_type"] = "Material Change"
    elif "package" in text_lower:
        parsed["change_type"] = "Package Change"
    elif "site" in text_lower or "factory" in text_lower:
        parsed["change_type"] = "Site Change"
    elif "specification" in text_lower or "spec" in text_lower:
        parsed["change_type"] = "Specification Change"

    # Dates — try to grab labelled dates first, fall back to generic
    eff_match = re.search(r'[Ee]ffective\s*[Dd]ate[:\s]+(\d{4}[-/]\d{2}[-/]\d{2})', pcn_text)
    ltb_match = re.search(r'[Ll]ast\s*(?:[Tt]ime\s*)?[Bb]uy\s*[Dd]ate[:\s]+(\d{4}[-/]\d{2}[-/]\d{2})', pcn_text)
    if eff_match:
        parsed["effective_date"] = eff_match.group(1)
    if ltb_match:
        parsed["last_buy_date"] = ltb_match.group(1)
    # Fallback if labelled dates not found
    if not parsed["effective_date"] or not parsed["last_buy_date"]:
        date_matches = re.findall(
            r'(\d{4}[-/]\d{2}[-/]\d{2})',
            pcn_text
        )
        if date_matches and not parsed["effective_date"]:
            parsed["effective_date"] = date_matches[0]
        if len(date_matches) > 1 and not parsed["last_buy_date"]:
            parsed["last_buy_date"] = date_matches[1]

    # Summary — first meaningful sentence
    sentences = [s.strip() for s in re.split(r'[.\n]', pcn_text) if s.strip()]
    parsed["summary"] = sentences[0][:200] if sentences else pcn_text[:200]

    return {**state, "parsed_pcn": parsed, "errors": errors, "status": "pcn_parsed"}


def query_kg(state: AgentState) -> AgentState:
    """Find assemblies affected by the PCN-listed components."""
    kg: BOMKnowledgeGraph = state["kg"]
    parsed = state.get("parsed_pcn", {})
    affected_parts = parsed.get("affected_parts", [])
    errors = list(state.get("errors", []))

    all_affected: List[dict] = []
    for part in affected_parts:
        assemblies = kg.get_affected_assemblies(part)
        comp = kg.get_component_details(part)
        for asm in assemblies:
            entry = {
                "part_number": part,
                "assembly": asm["id"],
                "ref_des": asm.get("ref_des", ""),
                "platform": asm.get("platform", ""),
                "certification": asm.get("certification", ""),
                "component_description": comp.get("description", "") if comp else "",
                "component_package": comp.get("package", "") if comp else "",
            }
            all_affected.append(entry)

    if not all_affected and affected_parts:
        errors.append(f"Parts {affected_parts} not found in knowledge graph")

    return {**state, "affected_assemblies": all_affected, "errors": errors,
            "status": "kg_queried"}


def find_alternates(state: AgentState) -> AgentState:
    """Search the KG for drop-in replacements for each affected part."""
    kg: BOMKnowledgeGraph = state["kg"]
    parsed = state.get("parsed_pcn", {})
    affected_parts = parsed.get("affected_parts", [])

    alternates: Dict[str, list] = {}
    for part in affected_parts:
        alts = kg.find_alternates(part)
        alternates[part] = [
            {
                "part_number": a["id"],
                "drop_in": a.get("drop_in", False),
                "qualification_status": a.get("qualification_status", "Unknown"),
                "notes": a.get("notes", ""),
                "description": a.get("description", ""),
            }
            for a in alts
        ]

    return {**state, "alternates": alternates, "status": "alternates_found"}


def assess_risk(state: AgentState) -> AgentState:
    """Evaluate overall risk based on affected assemblies, standards, and tests."""
    kg: BOMKnowledgeGraph = state["kg"]
    affected = state.get("affected_assemblies", [])
    alternates = state.get("alternates", {})
    parsed = state.get("parsed_pcn", {})

    risk: Dict[str, Any] = {
        "overall_severity": Severity.LOW.value,
        "factors": [],
        "affected_count": len(affected),
        "parts_without_alternates": [],
        "standards_at_risk": [],
        "test_evidence_impact": [],
        "recommendations": [],
    }

    # Count unique assemblies and parts
    unique_assemblies = set(a["assembly"] for a in affected)
    unique_parts = set(a["part_number"] for a in affected)
    severity_score = 0

    # Factor 1: Number of affected assemblies
    if len(unique_assemblies) >= 3:
        risk["factors"].append("Multiple assemblies affected (≥3)")
        severity_score += 3
    elif len(unique_assemblies) >= 2:
        risk["factors"].append("Two assemblies affected")
        severity_score += 2
    elif len(unique_assemblies) == 1:
        risk["factors"].append("Single assembly affected")
        severity_score += 1

    # Factor 2: Change type severity
    change_type = parsed.get("change_type", "")
    if change_type in ("Obsolescence", "Obsolete"):
        risk["factors"].append("Obsolescence — component no longer available")
        severity_score += 3
    elif change_type in ("Material Change", "Process Change"):
        risk["factors"].append(f"{change_type} — requalification may be needed")
        severity_score += 2
    else:
        risk["factors"].append(f"{change_type} — review needed")
        severity_score += 1

    # Factor 3: Alternate availability
    for part in unique_parts:
        alts = alternates.get(part, [])
        qualified = [a for a in alts if a.get("qualification_status") == "Qualified"]
        if not alts:
            risk["parts_without_alternates"].append(part)
            risk["factors"].append(f"No alternates registered for {part}")
            severity_score += 3
        elif not qualified:
            risk["factors"].append(f"Alternates for {part} exist but none qualified")
            severity_score += 2
        else:
            risk["factors"].append(f"{len(qualified)} qualified alternate(s) for {part}")

    # Factor 4: Standards compliance impact
    for asm_name in unique_assemblies:
        stds = kg.get_standards_for_assembly(asm_name)
        for std in stds:
            risk["standards_at_risk"].append({
                "assembly": asm_name,
                "standard": std.get("name", std["id"]),
                "version": std.get("version", ""),
            })
    if risk["standards_at_risk"]:
        risk["factors"].append(
            f"{len(risk['standards_at_risk'])} standard(s) may need re-certification"
        )
        severity_score += 2

    # Factor 5: Test evidence
    for part in unique_parts:
        tests = kg.get_test_evidence(part)
        for t in tests:
            risk["test_evidence_impact"].append({
                "part": part,
                "test_id": t.get("test_id", t["id"]),
                "test_type": t.get("test_type", ""),
                "result": t.get("result", ""),
            })
    if risk["test_evidence_impact"]:
        risk["factors"].append(
            f"{len(risk['test_evidence_impact'])} test report(s) may be invalidated"
        )
        severity_score += 1

    # Map score → severity
    if severity_score >= 8:
        risk["overall_severity"] = Severity.CRITICAL.value
    elif severity_score >= 5:
        risk["overall_severity"] = Severity.HIGH.value
    elif severity_score >= 3:
        risk["overall_severity"] = Severity.MEDIUM.value
    else:
        risk["overall_severity"] = Severity.LOW.value

    # Recommendations
    if risk["parts_without_alternates"]:
        risk["recommendations"].append(
            "Initiate urgent alternate qualification for: "
            + ", ".join(risk["parts_without_alternates"])
        )
    if risk["standards_at_risk"]:
        risk["recommendations"].append(
            "Schedule re-certification review with TÜV / notified body"
        )
    if risk["test_evidence_impact"]:
        risk["recommendations"].append(
            "Re-run affected tests with replacement components"
        )
    if change_type in ("Obsolescence",):
        risk["recommendations"].append(
            "Place last-time-buy order before deadline"
        )
    risk["recommendations"].append(
        "Update BOM and AVL documentation"
    )

    return {**state, "risk_assessment": risk, "status": "risk_assessed"}


def generate_report(state: AgentState) -> AgentState:
    """Produce a structured CCE-style report dict."""
    parsed = state.get("parsed_pcn", {})
    affected = state.get("affected_assemblies", [])
    alternates = state.get("alternates", {})
    risk = state.get("risk_assessment", {})

    report = {
        "title": f"PCN Impact Analysis Report",
        "generated_at": datetime.now().isoformat(),
        "pcn_summary": {
            "affected_parts": parsed.get("affected_parts", []),
            "change_type": parsed.get("change_type", "Unknown"),
            "effective_date": parsed.get("effective_date", ""),
            "last_buy_date": parsed.get("last_buy_date", ""),
            "summary": parsed.get("summary", ""),
        },
        "impact_analysis": {
            "total_affected_assemblies": len(set(a["assembly"] for a in affected)),
            "total_affected_components": len(set(a["part_number"] for a in affected)),
            "affected_details": affected,
        },
        "alternate_components": alternates,
        "risk_assessment": {
            "overall_severity": risk.get("overall_severity", "Unknown"),
            "severity_factors": risk.get("factors", []),
            "standards_at_risk": risk.get("standards_at_risk", []),
            "test_evidence_impact": risk.get("test_evidence_impact", []),
            "parts_without_alternates": risk.get("parts_without_alternates", []),
        },
        "recommendations": risk.get("recommendations", []),
        "errors": state.get("errors", []),
    }

    return {**state, "report": report, "status": "report_generated"}


# ── Conditional edges ────────────────────────────────────────────────────────

def should_find_alternates(state: AgentState) -> str:
    """If affected assemblies exist → find alternates; else → generate report."""
    if state.get("affected_assemblies"):
        return "find_alternates"
    return "generate_report"


def should_assess_risk(state: AgentState) -> str:
    return "assess_risk"


# ── Build the graph ──────────────────────────────────────────────────────────

def build_agent() -> Any:
    """Build and compile the LangGraph state machine."""
    workflow = StateGraph(AgentState)

    workflow.add_node("parse_pcn", parse_pcn)
    workflow.add_node("query_kg", query_kg)
    workflow.add_node("find_alternates", find_alternates)
    workflow.add_node("assess_risk", assess_risk)
    workflow.add_node("generate_report", generate_report)

    workflow.set_entry_point("parse_pcn")
    workflow.add_edge("parse_pcn", "query_kg")
    workflow.add_conditional_edges("query_kg", should_find_alternates,
                                  {"find_alternates": "find_alternates",
                                   "generate_report": "generate_report"})
    workflow.add_edge("find_alternates", "assess_risk")
    workflow.add_edge("assess_risk", "generate_report")
    workflow.add_edge("generate_report", END)

    return workflow.compile()


# ── Public API ───────────────────────────────────────────────────────────────

def analyze_pcn(pcn_text: str, kg: BOMKnowledgeGraph | None = None) -> dict:
    """Run the full agent pipeline.  Returns the report dict."""
    if kg is None:
        kg = build_demo_graph()
    agent = build_agent()
    initial_state: AgentState = {
        "pcn_text": pcn_text,
        "kg": kg,
        "errors": [],
        "status": "started",
    }
    result = agent.invoke(initial_state)
    return result.get("report", {})


# ── CLI self-test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sample_pcn = """
    Product Change Notification
    PCN Number: PCN-2025-0042
    Date: 2025-03-15

    Dear Customer,

    We regret to inform you that the following component will be discontinued:

    Part Number: G2R1000MT33J
    Description: Thick Film Resistor 100 Ohm 0.125W 0402 ±5%
    Change Type: Obsolescence / End of Life
    Effective Date: 2025-06-01
    Last Time Buy Date: 2025-05-01

    Recommended replacement: RC0402FR-07100RL

    Please contact your sales representative for further information.

    Regards,
    Yageo Corporation
    """

    print("Running BOM LangGraph Agent …\n")
    report = analyze_pcn(sample_pcn)
    print(json.dumps(report, indent=2))
