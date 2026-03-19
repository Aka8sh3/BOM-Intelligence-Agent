"""
BOM Knowledge Graph Schema — NetworkX Implementation
=====================================================
Complete knowledge graph for PCBA BOM management with:
  • 7 node types:  Component, Assembly, Supplier, Alternate,
                   PCNChange, Standard, TestEvidence
  • 9 edge types:  used-in, supplied-by, alternate-for, affected-by,
                   complies-with, tested-by, part-of, derived-from, references
  • CSV BOM loader, PCN ingestion, impact queries, alternate finder
  • JSON export for visualization

Runs on NetworkX (no DB setup).  Swap to Neo4j for production.
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx


# ── Enums ────────────────────────────────────────────────────────────────────

class NodeType(str, Enum):
    COMPONENT     = "Component"
    ASSEMBLY      = "Assembly"
    SUPPLIER      = "Supplier"
    ALTERNATE     = "Alternate"
    PCN_CHANGE    = "PCNChange"
    STANDARD      = "Standard"
    TEST_EVIDENCE = "TestEvidence"


class EdgeType(str, Enum):
    USED_IN       = "used-in"
    SUPPLIED_BY   = "supplied-by"
    ALTERNATE_FOR = "alternate-for"
    AFFECTED_BY   = "affected-by"
    COMPLIES_WITH = "complies-with"
    TESTED_BY     = "tested-by"
    PART_OF       = "part-of"
    DERIVED_FROM  = "derived-from"
    REFERENCES    = "references"


class Lifecycle(str, Enum):
    ACTIVE        = "Active"
    NRND          = "NRND"        # Not Recommended for New Design
    OBSOLETE      = "Obsolete"
    EOL           = "EOL"         # End-of-Life
    PRELIMINARY   = "Preliminary"


class ChangeType(str, Enum):
    OBSOLESCENCE   = "Obsolescence"
    PROCESS_CHANGE = "Process Change"
    MATERIAL_CHANGE = "Material Change"
    PACKAGE_CHANGE = "Package Change"
    SITE_CHANGE    = "Site Change"
    SPECIFICATION  = "Specification Change"


class Severity(str, Enum):
    CRITICAL = "Critical"
    HIGH     = "High"
    MEDIUM   = "Medium"
    LOW      = "Low"


# ── Knowledge Graph ──────────────────────────────────────────────────────────

class BOMKnowledgeGraph:
    """Full-featured knowledge graph for BOM / PCN analysis."""

    def __init__(self):
        self.G = nx.DiGraph()
        self._id_counter = 0

    # ── helpers ──────────────────────────────────────────────────────────

    def _next_id(self, prefix: str = "n") -> str:
        self._id_counter += 1
        return f"{prefix}_{self._id_counter}"

    # ── node CRUD ────────────────────────────────────────────────────────

    def add_component(self, part_number: str, **props) -> str:
        """Add or update a Component node.  Returns node id (= part_number)."""
        nid = part_number
        defaults = {
            "node_type": NodeType.COMPONENT,
            "part_number": part_number,
            "description": "",
            "package": "",
            "value": "",
            "voltage_rating": "",
            "current_rating": "",
            "temperature_range": "",
            "lifecycle": Lifecycle.ACTIVE,
            "datasheet_url": "",
            "rohs_compliant": True,
            "reach_compliant": True,
        }
        defaults.update(props)
        if nid in self.G:
            self.G.nodes[nid].update(defaults)
        else:
            self.G.add_node(nid, **defaults)
        return nid

    def add_assembly(self, name: str, **props) -> str:
        nid = name
        defaults = {
            "node_type": NodeType.ASSEMBLY,
            "name": name,
            "revision": "A",
            "platform": "",
            "product_line": "",
            "certification": "",
        }
        defaults.update(props)
        if nid in self.G:
            self.G.nodes[nid].update(defaults)
        else:
            self.G.add_node(nid, **defaults)
        return nid

    def add_supplier(self, name: str, **props) -> str:
        nid = f"SUP_{name}"
        defaults = {
            "node_type": NodeType.SUPPLIER,
            "name": name,
            "qualified": True,
            "country": "",
            "lead_time_weeks": 0,
        }
        defaults.update(props)
        if nid not in self.G:
            self.G.add_node(nid, **defaults)
        return nid

    def add_alternate(self, part_number: str, for_part: str, **props) -> str:
        """Register *part_number* as an alternate for *for_part*."""
        nid = part_number
        defaults = {
            "node_type": NodeType.ALTERNATE,
            "part_number": part_number,
            "drop_in": True,
            "qualification_status": "Pending",
            "notes": "",
        }
        defaults.update(props)
        if nid not in self.G:
            self.G.add_node(nid, **defaults)
        self.G.add_edge(nid, for_part, edge_type=EdgeType.ALTERNATE_FOR,
                        drop_in=defaults.get("drop_in", True),
                        qualification_status=defaults.get("qualification_status", "Pending"))
        return nid

    def add_pcn_change(self, pcn_id: str, **props) -> str:
        nid = f"PCN_{pcn_id}"
        defaults = {
            "node_type": NodeType.PCN_CHANGE,
            "pcn_id": pcn_id,
            "title": "",
            "change_type": ChangeType.OBSOLESCENCE,
            "effective_date": "",
            "last_buy_date": "",
            "description": "",
            "source_url": "",
        }
        defaults.update(props)
        if nid not in self.G:
            self.G.add_node(nid, **defaults)
        return nid

    def add_standard(self, name: str, **props) -> str:
        nid = f"STD_{name}"
        defaults = {
            "node_type": NodeType.STANDARD,
            "name": name,
            "version": "",
            "certification_body": "",
        }
        defaults.update(props)
        if nid not in self.G:
            self.G.add_node(nid, **defaults)
        return nid

    def add_test_evidence(self, test_id: str, **props) -> str:
        nid = f"TEST_{test_id}"
        defaults = {
            "node_type": NodeType.TEST_EVIDENCE,
            "test_id": test_id,
            "test_type": "",
            "result": "Pass",
            "date": "",
            "report_url": "",
        }
        defaults.update(props)
        if nid not in self.G:
            self.G.add_node(nid, **defaults)
        return nid

    # ── edge helpers ─────────────────────────────────────────────────────

    def link_component_to_assembly(self, part: str, assembly: str,
                                   ref_des: str = "", quantity: int = 1):
        self.G.add_edge(part, assembly,
                        edge_type=EdgeType.USED_IN,
                        ref_des=ref_des,
                        quantity=quantity)

    def link_component_to_supplier(self, part: str, supplier_nid: str):
        self.G.add_edge(part, supplier_nid,
                        edge_type=EdgeType.SUPPLIED_BY)

    def link_pcn_to_component(self, pcn_nid: str, part: str):
        self.G.add_edge(pcn_nid, part,
                        edge_type=EdgeType.AFFECTED_BY)

    def link_assembly_to_standard(self, assembly: str, std_nid: str):
        self.G.add_edge(assembly, std_nid,
                        edge_type=EdgeType.COMPLIES_WITH)

    def link_component_to_test(self, part: str, test_nid: str):
        self.G.add_edge(part, test_nid,
                        edge_type=EdgeType.TESTED_BY)

    def link_assembly_parent(self, child: str, parent: str):
        self.G.add_edge(child, parent,
                        edge_type=EdgeType.PART_OF)

    # ── BOM CSV/Excel loader ───────────────────────────────────────────────────

    def _normalize_row_keys(self, row_dict: dict) -> dict:
        """Map flexible BOM headers to standard schema keys."""
        norm_row = {}
        
        aliases = {
            "part_number": ["part_number", "part number", "mpn", "mfg p/n", "mfg part number", "manufacturer part number", "manufacturer part no", "mfg part no", "part no", "p/n", "part#", "component", "item", "part", "mfg_pn", "pn"],
            "manufacturer": ["manufacturer", "mfr", "mfg", "maker", "brand"],
            "description": ["description", "desc", "title", "part description"],
            "package": ["package", "footprint", "case", "size", "pkg"],
            "value": ["value", "val", "resistance", "capacitance", "rating", "tolerance"],
            "voltage_rating": ["voltage", "voltage rating", "v rating", "v_rating"],
            "lifecycle": ["lifecycle", "life cycle", "status", "part status", "rohs"],
            "platform": ["platform", "assembly", "project", "board"],
            "ref_des": ["ref_des", "designator", "reference", "ref des", "ref"]
        }
        
        for raw_k, v in row_dict.items():
            if not isinstance(raw_k, str):
                continue
                
            clean_k = raw_k.lower().strip().replace("_", " ")
            
            matched = False
            for std_key, alt_list in aliases.items():
                if clean_k in alt_list:
                    if std_key not in norm_row or not norm_row[std_key]:
                        norm_row[std_key] = str(v).strip() if v is not None else ""
                    matched = True
                    break
            
            if not matched:
                safe_k = raw_k.lower().strip().replace(" ", "_").replace("/", "_")
                norm_row[safe_k] = str(v).strip() if v is not None else ""

        return norm_row

    def load_bom_csv(self, path: str) -> dict:
        """Load a BOM CSV.  Expected columns:
        ref_des, part_number, description, manufacturer, package, value,
        voltage_rating, lifecycle, platform
        Returns summary dict and raw components.
        """
        components_added = 0
        assemblies_added: Set[str] = set()
        suppliers_added: Set[str] = set()
        raw_components = []

        with open(path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.reader(fh)
            headers = []
            header_found = False
            
            for row_idx, row in enumerate(reader):
                if not header_found:
                    row_strs = [str(c).lower().strip() for c in row if c]
                    row_text = " ".join(row_strs)
                    if any(kw in row_text for kw in ["part", "mpn", "description", "mfr", "manufacturer", "designator"]):
                        headers = [str(cell).strip() if cell else f"col_{i}" for i, cell in enumerate(row)]
                        header_found = True
                    continue
                
                if not headers:
                    continue
                    
                raw_dict = dict(zip(headers, [c for c in row]))
                row_dict = self._normalize_row_keys(raw_dict)
                
                pn = row_dict.get("part_number", "").strip()
                if not pn:
                    continue
                
                raw_components.append(row_dict)

                # Component
                self.add_component(
                    pn,
                    description=row_dict.get("description", ""),
                    package=row_dict.get("package", ""),
                    value=row_dict.get("value", ""),
                    voltage_rating=row_dict.get("voltage_rating", ""),
                    lifecycle=row_dict.get("lifecycle", Lifecycle.ACTIVE),
                )
                components_added += 1

                # Assembly (platform)
                platform = row_dict.get("platform", "").strip()
                if platform:
                    self.add_assembly(platform, platform=platform)
                    assemblies_added.add(platform)
                    self.link_component_to_assembly(
                        pn, platform,
                        ref_des=row_dict.get("ref_des", ""),
                    )

                # Supplier
                mfr = row_dict.get("manufacturer", "").strip()
                if mfr:
                    sid = self.add_supplier(mfr)
                    suppliers_added.add(mfr)
                    self.link_component_to_supplier(pn, sid)

        return {
            "summary": {
                "components": components_added,
                "assemblies": len(assemblies_added),
                "suppliers": len(suppliers_added),
            },
            "raw_components": raw_components
        }

    def load_bom_excel(self, path: str) -> dict:
        """Load a BOM Excel (.xlsx). Expects similar columns to CSV.
        Returns summary dict and raw components.
        """
        import openpyxl
        
        components_added = 0
        assemblies_added: Set[str] = set()
        suppliers_added: Set[str] = set()
        raw_components = []

        wb = openpyxl.load_workbook(path, data_only=True)
        sheet = wb.active
        
        headers = []
        header_found = False
        
        for row_idx, row in enumerate(sheet.iter_rows(values_only=True)):
            if not header_found:
                row_strs = [str(c).lower().strip() for c in row if c is not None]
                row_text = " ".join(row_strs)
                if any(kw in row_text for kw in ["part", "mpn", "description", "mfr", "manufacturer", "designator"]):
                    headers = [str(cell).strip() if cell else f"col_{i}" for i, cell in enumerate(row)]
                    header_found = True
                continue
                
            if not headers:
                continue
                
            raw_dict = dict(zip(headers, [c for c in row]))
            row_dict = self._normalize_row_keys(raw_dict)
            
            pn = row_dict.get("part_number", "").strip()
            if not pn:
                continue
                
            raw_components.append(row_dict)

            # Component
            self.add_component(
                pn,
                description=row_dict.get("description", ""),
                package=row_dict.get("package", ""),
                value=row_dict.get("value", ""),
                voltage_rating=row_dict.get("voltage_rating", ""),
                lifecycle=row_dict.get("lifecycle", Lifecycle.ACTIVE),
            )
            components_added += 1

            # Assembly
            platform = row_dict.get("platform", "").strip()
            if platform:
                self.add_assembly(platform, platform=platform)
                assemblies_added.add(platform)
                self.link_component_to_assembly(
                    pn, platform,
                    ref_des=row_dict.get("ref_des", ""),
                )

            # Supplier
            mfr = row_dict.get("manufacturer", "").strip()
            if mfr:
                sid = self.add_supplier(mfr)
                suppliers_added.add(mfr)
                self.link_component_to_supplier(pn, sid)

        return {
            "summary": {
                "components": components_added,
                "assemblies": len(assemblies_added),
                "suppliers": len(suppliers_added),
            },
            "raw_components": raw_components
        }

    # ── PCN ingestion ────────────────────────────────────────────────────

    def ingest_pcn(self, pcn_id: str, affected_parts: List[str],
                   change_type: str = "Obsolescence",
                   effective_date: str = "",
                   description: str = "") -> str:
        """Create a PCNChange node and link it to affected components."""
        nid = self.add_pcn_change(
            pcn_id,
            change_type=change_type,
            effective_date=effective_date,
            description=description,
            title=f"PCN {pcn_id}",
        )
        for pn in affected_parts:
            if pn in self.G:
                self.link_pcn_to_component(nid, pn)
                # Mark lifecycle
                self.G.nodes[pn]["lifecycle"] = Lifecycle.OBSOLETE
        return nid

    # ── queries ──────────────────────────────────────────────────────────

    def get_affected_assemblies(self, part_number: str) -> List[dict]:
        """Return every assembly that uses *part_number*."""
        results = []
        if part_number not in self.G:
            return results
        for _, target, data in self.G.edges(part_number, data=True):
            if data.get("edge_type") == EdgeType.USED_IN:
                node = dict(self.G.nodes[target])
                node["id"] = target
                node["ref_des"] = data.get("ref_des", "")
                results.append(node)
        return results

    def find_alternates(self, part_number: str) -> List[dict]:
        """Return registered alternates for *part_number*."""
        results = []
        for source, target, data in self.G.edges(data=True):
            if (data.get("edge_type") == EdgeType.ALTERNATE_FOR
                    and target == part_number):
                node = dict(self.G.nodes[source])
                node["id"] = source
                node["drop_in"] = data.get("drop_in", True)
                node["qualification_status"] = data.get("qualification_status", "Pending")
                results.append(node)
        return results

    def get_component_details(self, part_number: str) -> Optional[dict]:
        if part_number in self.G:
            d = dict(self.G.nodes[part_number])
            d["id"] = part_number
            return d
        return None

    def get_standards_for_assembly(self, assembly: str) -> List[dict]:
        results = []
        if assembly not in self.G:
            return results
        for _, target, data in self.G.edges(assembly, data=True):
            if data.get("edge_type") == EdgeType.COMPLIES_WITH:
                node = dict(self.G.nodes[target])
                node["id"] = target
                results.append(node)
        return results

    def get_test_evidence(self, part_number: str) -> List[dict]:
        results = []
        if part_number not in self.G:
            return results
        for _, target, data in self.G.edges(part_number, data=True):
            if data.get("edge_type") == EdgeType.TESTED_BY:
                node = dict(self.G.nodes[target])
                node["id"] = target
                results.append(node)
        return results

    # ── export ───────────────────────────────────────────────────────────

    def to_json(self) -> dict:
        """Export full graph as JSON-serialisable dict."""
        nodes = []
        for nid, data in self.G.nodes(data=True):
            d = {k: (v.value if isinstance(v, Enum) else v) for k, v in data.items()}
            d["id"] = nid
            nodes.append(d)

        edges = []
        for src, tgt, data in self.G.edges(data=True):
            d = {k: (v.value if isinstance(v, Enum) else v) for k, v in data.items()}
            d["source"] = src
            d["target"] = tgt
            edges.append(d)

        return {"nodes": nodes, "edges": edges}

    def summary(self) -> dict:
        type_counts: dict[str, int] = {}
        for _, data in self.G.nodes(data=True):
            t = data.get("node_type", "Unknown")
            label = t.value if isinstance(t, Enum) else str(t)
            type_counts[label] = type_counts.get(label, 0) + 1
        return {
            "total_nodes": self.G.number_of_nodes(),
            "total_edges": self.G.number_of_edges(),
            "node_types": type_counts,
        }


# ── Seed demo data ───────────────────────────────────────────────────────────

def build_demo_graph() -> BOMKnowledgeGraph:
    """Build a populated demo graph for testing / demo purposes."""
    kg = BOMKnowledgeGraph()
    csv_path = os.path.join(os.path.dirname(__file__), "sample_bom.csv")
    if os.path.exists(csv_path):
        kg.load_bom_csv(csv_path)
    else:
        # Inline fallback
        kg.add_assembly("CARDIOHELP", platform="CARDIOHELP",
                        product_line="Heart-Lung Support",
                        certification="MDR Class IIb")
        kg.add_assembly("ROTAFLOW", platform="ROTAFLOW",
                        product_line="Centrifugal Pump",
                        certification="MDR Class IIb")

        kg.add_component("G2R1000MT33J", description="Thick Film Resistor 100Ω 0402",
                         package="0402", value="100 Ohm", voltage_rating="50V",
                         lifecycle=Lifecycle.ACTIVE)
        kg.add_component("1ED3241MC12H", description="Gate Driver IC Single Channel",
                         package="PG-DSO-8", voltage_rating="1200V",
                         lifecycle=Lifecycle.ACTIVE)

        sup_yageo = kg.add_supplier("Yageo")
        sup_inf = kg.add_supplier("Infineon")

        kg.link_component_to_assembly("G2R1000MT33J", "CARDIOHELP", ref_des="R101")
        kg.link_component_to_assembly("G2R1000MT33J", "ROTAFLOW", ref_des="R102")
        kg.link_component_to_assembly("1ED3241MC12H", "CARDIOHELP", ref_des="U101")
        kg.link_component_to_assembly("1ED3241MC12H", "ROTAFLOW", ref_des="U102")

        kg.link_component_to_supplier("G2R1000MT33J", sup_yageo)
        kg.link_component_to_supplier("1ED3241MC12H", sup_inf)

    # Register known alternates
    kg.add_alternate("RC0402FR-07100RL", "G2R1000MT33J",
                     drop_in=True, qualification_status="Qualified",
                     notes="Same 0402, 100Ω, 50V, Yageo thick-film")
    kg.add_alternate("CRCW0402100RFKED", "G2R1000MT33J",
                     drop_in=True, qualification_status="Pending",
                     notes="Vishay 0402 100Ω — footprint compatible")
    kg.add_alternate("1EDI20I12MH", "1ED3241MC12H",
                     drop_in=True, qualification_status="Qualified",
                     notes="Infineon pin-compatible gate driver")

    # Standards
    std_mdr = kg.add_standard("IEC 60601-1", version="3.2",
                              certification_body="TÜV SÜD")
    std_emc = kg.add_standard("IEC 61000-4-3", version="2014",
                              certification_body="TÜV SÜD")
    kg.link_assembly_to_standard("CARDIOHELP", std_mdr)
    kg.link_assembly_to_standard("CARDIOHELP", std_emc)
    kg.link_assembly_to_standard("ROTAFLOW", std_mdr)

    # Test evidence
    t1 = kg.add_test_evidence("EMC-2024-001", test_type="EMC Radiated Emissions",
                              result="Pass", date="2024-03-15")
    t2 = kg.add_test_evidence("ENV-2024-002", test_type="Thermal Cycling -40/+85°C",
                              result="Pass", date="2024-01-20")
    kg.link_component_to_test("G2R1000MT33J", t1)
    kg.link_component_to_test("G2R1000MT33J", t2)
    kg.link_component_to_test("1ED3241MC12H", t1)

    return kg


# ── CLI self-test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Building demo knowledge graph …")
    kg = build_demo_graph()
    s = kg.summary()
    print(f"  Nodes: {s['total_nodes']}  Edges: {s['total_edges']}")
    print(f"  By type: {json.dumps(s['node_types'], indent=2)}")

    print("\n— Impact query: G2R1000MT33J —")
    for asm in kg.get_affected_assemblies("G2R1000MT33J"):
        print(f"  Assembly: {asm['id']}  (ref {asm.get('ref_des','')})")

    print("\n— Alternates for G2R1000MT33J —")
    for alt in kg.find_alternates("G2R1000MT33J"):
        print(f"  {alt['id']}  drop-in={alt['drop_in']}  status={alt['qualification_status']}")

    print("\n— Alternates for 1ED3241MC12H —")
    for alt in kg.find_alternates("1ED3241MC12H"):
        print(f"  {alt['id']}  drop-in={alt['drop_in']}  status={alt['qualification_status']}")

    print("\n— Standards for CARDIOHELP —")
    for std in kg.get_standards_for_assembly("CARDIOHELP"):
        print(f"  {std['id']}  {std.get('name','')}  v{std.get('version','')}")

    print("\n— Test evidence for G2R1000MT33J —")
    for te in kg.get_test_evidence("G2R1000MT33J"):
        print(f"  {te['id']}  {te.get('test_type','')}  result={te.get('result','')}")

    print("\nDone ✓")
