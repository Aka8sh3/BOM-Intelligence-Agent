"""
Component Search Engine
========================
Orchestrates LLM-powered component intelligence:
  - Lifecycle status (Active / NRND / EOL / Obsolete)
  - Vendor pricing from major distributors
  - Stock availability
  - PCN / PDN / EOL detection
  - Alternative component suggestions with comparison
"""

from __future__ import annotations

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from llm_engine import (
    llm_analyze_component,
    llm_find_alternatives,
)


# Thread pool for parallel LLM calls
_executor = ThreadPoolExecutor(max_workers=4)


def analyze_single_component(component: dict) -> dict:
    """Analyze a single component — called for each row in the BOM.
    
    Args:
        component: dict with keys like part_number, description, manufacturer, package
    
    Returns:
        Enriched component dict with LLM analysis data.
    """
    pn = component.get("part_number", "")
    if not pn:
        return component

    # Add a small delay to prevent NVIDIA 429 rate limit errors
    import time
    time.sleep(2)

    # Run LLM analysis
    analysis = llm_analyze_component(
        part_number=pn,
        description=component.get("description", ""),
        manufacturer=component.get("manufacturer", ""),
        package=component.get("package", ""),
    )

    # Merge analysis into component
    enriched = {**component}
    enriched["analysis"] = analysis
    enriched["lifecycle_status"] = analysis.get("lifecycle_status", "Unknown")
    enriched["availability"] = analysis.get("availability", "Unknown")
    enriched["risk_level"] = analysis.get("risk_level", "Medium")
    enriched["vendors"] = analysis.get("vendors", [])
    enriched["typical_price_usd"] = analysis.get("typical_price_usd", "Unknown")
    enriched["pcn_pdn_status"] = analysis.get("pcn_pdn_status", {})
    enriched["alternatives"] = analysis.get("alternatives", [])
    enriched["specifications"] = analysis.get("specifications", {})
    enriched["notes"] = analysis.get("notes", "")

    return enriched


from concurrent.futures import ThreadPoolExecutor, as_completed

def analyze_bom_components(components: List[dict],
                           progress_callback=None) -> dict:
    """Analyze all components in a BOM in parallel.
    
    Args:
        components: list of component dicts from BOM
        progress_callback: optional callable(current, total, component_name)
    
    Returns:
        Full analysis result dict with dashboard data.
    """
    total = len(components)
    analyzed = []
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_comp = {executor.submit(analyze_single_component, comp): comp for comp in components}
        
        completed_count = 0
        for future in as_completed(future_to_comp):
            comp = future_to_comp[future]
            try:
                enriched = future.result()
                analyzed.append(enriched)
            except Exception as exc:
                enriched = {**comp}
                enriched["lifecycle_status"] = "Unknown"
                enriched["availability"] = "Unknown"
                enriched["risk_level"] = "Medium"
                analyzed.append(enriched)
                
            completed_count += 1
            if progress_callback:
                progress_callback(completed_count, total, comp.get("part_number", ""))

    # Build dashboard summary data
    return _build_dashboard_data(analyzed)


def _build_dashboard_data(components: List[dict]) -> dict:
    """Aggregate component analyses into dashboard-ready data."""
    
    total = len(components)
    
    # Lifecycle distribution
    lifecycle_counts = {"Active": 0, "NRND": 0, "EOL": 0, "Obsolete": 0, "Unknown": 0}
    for c in components:
        status = c.get("lifecycle_status", "Unknown")
        if status in lifecycle_counts:
            lifecycle_counts[status] += 1
        else:
            lifecycle_counts["Unknown"] += 1
    
    # Availability distribution
    availability_counts = {"In Stock": 0, "Limited": 0, "Out of Stock": 0, "Unknown": 0}
    for c in components:
        avail = c.get("availability", "Unknown")
        if avail in availability_counts:
            availability_counts[avail] += 1
        else:
            availability_counts["Unknown"] += 1
    
    # Risk distribution
    risk_counts = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    for c in components:
        risk = c.get("risk_level", "Medium")
        if risk in risk_counts:
            risk_counts[risk] += 1
        else:
            risk_counts["Medium"] += 1
    
    # Components with issues
    issues = []
    for c in components:
        pn = c.get("part_number", "")
        lifecycle = c.get("lifecycle_status", "Unknown")
        avail = c.get("availability", "Unknown")
        pcn = c.get("pcn_pdn_status", {})
        
        if lifecycle in ("EOL", "Obsolete"):
            issues.append({
                "part_number": pn,
                "issue_type": "Lifecycle",
                "severity": "Critical" if lifecycle == "Obsolete" else "High",
                "description": f"Component is {lifecycle}",
                "has_alternatives": len(c.get("alternatives", [])) > 0,
            })
        if avail == "Out of Stock":
            issues.append({
                "part_number": pn,
                "issue_type": "Availability",
                "severity": "High",
                "description": "Component is out of stock",
                "has_alternatives": len(c.get("alternatives", [])) > 0,
            })
        if pcn.get("has_active_pcn") or pcn.get("has_pdn"):
            issues.append({
                "part_number": pn,
                "issue_type": "PCN/PDN",
                "severity": "High",
                "description": pcn.get("notice_summary", "Active notice detected"),
                "has_alternatives": len(c.get("alternatives", [])) > 0,
            })
        if pcn.get("is_eol"):
            issues.append({
                "part_number": pn,
                "issue_type": "End of Life",
                "severity": "Critical",
                "description": "Component has reached End of Life",
                "has_alternatives": len(c.get("alternatives", [])) > 0,
            })
    
    # Vendor pricing aggregation
    all_vendors = {}
    for c in components:
        for v in c.get("vendors", []):
            vname = v.get("name", "Unknown")
            if vname not in all_vendors:
                all_vendors[vname] = {"name": vname, "components_available": 0, "components_total": total}
            if v.get("stock") in ("In Stock", "Limited"):
                all_vendors[vname]["components_available"] += 1
    
    # Unique parts with alternatives
    parts_with_alts = sum(1 for c in components if c.get("alternatives"))
    total_alternatives = sum(len(c.get("alternatives", [])) for c in components)
    
    # Overall health score (0-100)
    active_pct = lifecycle_counts["Active"] / max(total, 1) * 100
    instock_pct = availability_counts["In Stock"] / max(total, 1) * 100
    health_score = int((active_pct * 0.5 + instock_pct * 0.5))
    
    # Overall risk
    if risk_counts["Critical"] > 0:
        overall_risk = "Critical"
    elif risk_counts["High"] > 0:
        overall_risk = "High"
    elif risk_counts["Medium"] > total * 0.3:
        overall_risk = "Medium"
    else:
        overall_risk = "Low"

    return {
        "summary": {
            "total_components": total,
            "unique_parts": len(set(c.get("part_number", "") for c in components)),
            "health_score": health_score,
            "overall_risk": overall_risk,
            "parts_with_alternatives": parts_with_alts,
            "total_alternatives_found": total_alternatives,
            "total_issues": len(issues),
        },
        "lifecycle_distribution": lifecycle_counts,
        "availability_distribution": availability_counts,
        "risk_distribution": risk_counts,
        "vendor_coverage": list(all_vendors.values()),
        "issues": issues,
        "components": components,
    }
