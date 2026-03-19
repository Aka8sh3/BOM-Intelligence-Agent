"""
LLM Engine — NVIDIA API Integration
====================================
Uses NVIDIA's OpenAI-compatible API (integrate.api.nvidia.com/v1)
for intelligent component analysis, alternative suggestions, and PCN parsing.
"""

from __future__ import annotations

import os
import json
from typing import Optional

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

_llm = None


def get_llm():
    """Get or create the NVIDIA LLM client."""
    global _llm
    if _llm is not None:
        return _llm

    api_key = os.environ.get("NVIDIA_API_KEY", "")
    if not api_key:
        return None

    try:
        from langchain_openai import ChatOpenAI
        _llm = ChatOpenAI(
            model="moonshotai/kimi-k2.5",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
            temperature=1.0,
            top_p=1.0
        )
        return _llm
    except Exception as e:
        print(f"[LLM] Failed to initialize: {e}")
        return None


def llm_analyze_component(part_number: str, description: str = "",
                          manufacturer: str = "", package: str = "") -> dict:
    """Use LLM to analyze a component's availability, pricing, lifecycle, and vendors."""
    llm = get_llm()
    if not llm:
        return _fallback_component_analysis(part_number, description, manufacturer)

    prompt = f"""You are an expert electronics component analyst. Analyze this component and return a JSON object.

Component: {part_number}
Description: {description}
Manufacturer: {manufacturer}
Package: {package}

Return ONLY valid JSON (no markdown, no code blocks) with this exact structure:
{{
    "part_number": "{part_number}",
    "lifecycle_status": "Active|NRND|EOL|Obsolete|Unknown",
    "availability": "In Stock|Limited|Out of Stock|Unknown",
    "risk_level": "Low|Medium|High|Critical",
    "estimated_stock": "quantity estimate or 'Unknown'",
    "typical_price_usd": "price per unit or 'Unknown'",
    "vendors": [
        {{"name": "vendor name", "price_usd": estimated_price, "stock": "In Stock|Out of Stock|Limited", "lead_time_days": estimated_days}},
    ],
    "pcn_pdn_status": {{
        "has_active_pcn": true/false,
        "has_pdn": true/false,
        "is_eol": true/false,
        "notice_summary": "brief description or empty"
    }},
    "alternatives": [
        {{
            "part_number": "alternative part number",
            "manufacturer": "manufacturer",
            "description": "brief description",
            "compatibility": "Drop-in|Pin-Compatible|Functional",
            "key_differences": "brief note on differences",
            "estimated_price_usd": price_or_null
        }}
    ],
    "specifications": {{
        "package": "{package}",
        "voltage_rating": "value or Unknown",
        "current_rating": "value or Unknown",
        "power_rating": "value or Unknown",
        "temperature_range": "value or Unknown",
        "tolerance": "value or Unknown"
    }},
    "notes": "any additional relevant information"
}}

Provide realistic data based on your knowledge of electronics components. Include at least 3-5 major distributors and 2-3 alternatives where applicable. For pricing, give realistic estimates in USD."""

    try:
        resp = llm.invoke(prompt)
        content = resp.content if hasattr(resp, "content") else str(resp)
        # Clean potential markdown wrapping
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        if content.startswith("json"):
            content = content[4:].strip()

        data = json.loads(content)
        data["source"] = "llm"
        return data
    except Exception as e:
        print(f"[LLM] Component analysis failed for {part_number}: {e}")
        return _fallback_component_analysis(part_number, description, manufacturer)


def llm_find_alternatives(part_number: str, description: str = "",
                          specs: dict = None) -> list:
    """Use LLM to find alternative components with detailed comparison."""
    llm = get_llm()
    if not llm:
        return []

    specs_str = json.dumps(specs, indent=2) if specs else "Not provided"
    prompt = f"""You are an expert electronics component engineer. Find alternative/replacement components for:

Part Number: {part_number}
Description: {description}
Specifications: {specs_str}

Return ONLY a valid JSON array (no markdown) of alternative components:
[
    {{
        "part_number": "exact MPN",
        "manufacturer": "name",
        "description": "brief",
        "compatibility": "Drop-in|Pin-Compatible|Functional",
        "package": "package type",
        "key_specs": {{
            "voltage_rating": "value",
            "current_rating": "value",
            "power_rating": "value",
            "temperature_range": "value"
        }},
        "advantages": ["list of advantages over original"],
        "disadvantages": ["list of disadvantages"],
        "estimated_price_usd": price,
        "confidence_score": 0.0-1.0
    }}
]

Provide 3-5 realistic alternatives ordered by compatibility score."""

    try:
        resp = llm.invoke(prompt)
        content = resp.content if hasattr(resp, "content") else str(resp)
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        if content.startswith("json"):
            content = content[4:].strip()
        return json.loads(content)
    except Exception as e:
        print(f"[LLM] Alternatives search failed for {part_number}: {e}")
        return []


def llm_parse_pcn(pcn_text: str) -> dict:
    """Use LLM to parse PCN/PDN text into structured data."""
    llm = get_llm()
    if not llm:
        return {}

    prompt = f"""Parse this Product Change Notification / Product Discontinuation Notice and return structured JSON.

PCN Text:
{pcn_text}

Return ONLY valid JSON:
{{
    "pcn_id": "notice ID",
    "affected_parts": ["list of part numbers"],
    "change_type": "Obsolescence|Process Change|Material Change|Package Change|Site Change|Specification Change",
    "effective_date": "date string",
    "last_buy_date": "date string or empty",
    "summary": "one-line summary",
    "impact_severity": "Critical|High|Medium|Low",
    "recommended_actions": ["list of recommended actions"]
}}"""

    try:
        resp = llm.invoke(prompt)
        content = resp.content if hasattr(resp, "content") else str(resp)
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        if content.startswith("json"):
            content = content[4:].strip()
        return json.loads(content)
    except Exception as e:
        print(f"[LLM] PCN parse failed: {e}")
        return {}


def _fallback_component_analysis(part_number: str, description: str = "",
                                  manufacturer: str = "") -> dict:
    """Rule-based fallback when LLM is unavailable."""
    return {
        "part_number": part_number,
        "lifecycle_status": "Unknown",
        "availability": "Unknown",
        "risk_level": "Medium",
        "estimated_stock": "Unknown",
        "typical_price_usd": "Unknown",
        "vendors": [
            {"name": "Digi-Key", "price_usd": None, "stock": "Unknown", "lead_time_days": None},
            {"name": "Mouser", "price_usd": None, "stock": "Unknown", "lead_time_days": None},
            {"name": "Newark", "price_usd": None, "stock": "Unknown", "lead_time_days": None},
        ],
        "pcn_pdn_status": {
            "has_active_pcn": False,
            "has_pdn": False,
            "is_eol": False,
            "notice_summary": ""
        },
        "alternatives": [],
        "specifications": {
            "package": "",
            "voltage_rating": "Unknown",
            "current_rating": "Unknown",
            "power_rating": "Unknown",
            "temperature_range": "Unknown",
            "tolerance": "Unknown",
        },
        "notes": "LLM unavailable — showing fallback data. Add NVIDIA_API_KEY to .env for full analysis.",
        "source": "fallback",
    }
