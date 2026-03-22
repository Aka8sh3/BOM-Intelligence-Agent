"""
FastAPI Server for BOM Change Impact Analyser v2
=================================================
Endpoints:
  POST /api/upload-bom       — upload a BOM CSV/Excel for full analysis
  GET  /api/analysis/{id}   — retrieve a cached analysis
  POST /api/search-component — on-demand single component analysis
  POST /api/find-alternatives— get alternatives for a single part
  WS   /ws/progress          — real-time progress updates during analysis
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import uuid
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from bom_kg_schema import BOMKnowledgeGraph, build_demo_graph
from component_search import analyze_bom_components, analyze_single_component
from llm_engine import llm_find_alternatives

# ── App setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="BOM Change Impact Analyser API v2",
    version="2.0.0",
    description="Enhanced all-in-one BOM intelligence platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Shared state ─────────────────────────────────────────────────────────────

_kg: BOMKnowledgeGraph = build_demo_graph()
_analyses: Dict[str, dict] = {}


def get_kg() -> BOMKnowledgeGraph:
    return _kg


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.active_connections.remove(connection)

manager = ConnectionManager()

# ── Request / response models ───────────────────────────────────────────────

class SearchComponentRequest(BaseModel):
    part_number: str
    description: str = ""
    manufacturer: str = ""
    package: str = ""

class FindAlternativesRequest(BaseModel):
    part_number: str
    description: str = ""
    specifications: Optional[dict] = None

# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    kg = get_kg()
    return {
        "status": "ok",
        "graph_summary": kg.summary(),
    }


@app.get("/api/graph")
async def get_graph():
    """Retrieve the intelligent BOM Knowledge graph native schema."""
    try:
        from falkordb import FalkorDB
        db = FalkorDB(host='localhost', port=6379, decode_responses=True)
        graph = db.select_graph("BOM_Intelligence")
        
        # Pull all edges which automatically fetch their source and target nodes
        res = graph.query("MATCH (n)-[r]->(m) RETURN n, r, m").result_set
        
        nodes_dict = {}
        links = []
        
        for record in res:
            n = record[0]
            r = record[1]
            m = record[2]
            
            for node in [n, m]:
                if node and node.id not in nodes_dict:
                    lbl = node.get_label()
                    props = node.properties or {}
                    name = props.get("name", "")
                    part_number = props.get("part_number", "")
                    desc = props.get("description", "")
                    manufacturer = props.get("manufacturer", "")
                    
                    nodes_dict[node.id] = {
                        "id": node.id,
                        "label": lbl,
                        "name": name or part_number,
                        "part_number": part_number,
                        "description": desc,
                        "manufacturer": manufacturer
                    }
            
            if r:
                r_props = r.properties or {}
                links.append({
                    "source": r.src_node,
                    "target": r.dest_node,
                    "label": r.relation,
                    "reasoning": r_props.get("reasoning", "")
                })
        
        # Also catch any isolated nodes
        isolated_res = graph.query("MATCH (n) WHERE NOT (n)--() RETURN n").result_set
        for record in isolated_res:
             node = record[0]
             if node and node.id not in nodes_dict:
                 lbl = node.get_label()
                 props = node.properties or {}
                 name = props.get("name", "")
                 part_number = props.get("part_number", "")
                 nodes_dict[node.id] = {
                     "id": node.id,
                     "label": lbl,
                     "name": name or part_number,
                     "part_number": part_number
                 }

        return {
            "success": True,
            "data": {
                "nodes": list(nodes_dict.values()),
                "links": links
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def _run_bg_analysis(analysis_id: str, raw_components: list, main_loop: asyncio.AbstractEventLoop):
    """Run analysis in the background and update global state."""
    # We are in a background thread provided by Starlette/FastAPI's BackgroundTasks
    
    def progress_callback(current, total, part_number):
        msg = {
            "type": "progress",
            "analysis_id": analysis_id,
            "current": current,
            "total": total,
            "part_number": part_number
        }
        # Safely broadcast to websockets from synchronous code
        try:
            asyncio.run_coroutine_threadsafe(manager.broadcast(msg), main_loop)
        except Exception:
            pass

    try:
        # Run synchronous analysis
        result = analyze_bom_components(raw_components, progress_callback)
        _analyses[analysis_id] = {
            "status": "complete",
            "result": result
        }
        try:
            asyncio.run_coroutine_threadsafe(
                manager.broadcast({
                    "type": "complete",
                    "analysis_id": analysis_id
                }),
                main_loop
            )
        except Exception:
            pass
    except Exception as e:
        _analyses[analysis_id] = {
            "status": "error",
            "error": str(e)
        }
        try:
            asyncio.run_coroutine_threadsafe(
                manager.broadcast({
                    "type": "error",
                    "analysis_id": analysis_id,
                    "error": str(e)
                }),
                main_loop
            )
        except Exception:
            pass


@app.post("/api/upload-bom")
async def api_upload_bom(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload a BOM (CSV/Excel) for full intelligence analysis."""
    filename = file.filename or ""
    is_csv = filename.endswith(".csv")
    is_excel = filename.endswith(".xlsx") or filename.endswith(".xls")
    
    if not (is_csv or is_excel):
        raise HTTPException(status_code=400, detail="File must be .csv or .xlsx")

    # Generate an ID for this analysis session
    analysis_id = str(uuid.uuid4())
    _analyses[analysis_id] = {"status": "processing"}

    try:
        contents = await file.read()
        suffix = ".csv" if is_csv else ".xlsx"
        with tempfile.NamedTemporaryFile(mode="wb", suffix=suffix, delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        kg = get_kg()
        if is_csv:
            load_result = kg.load_bom_csv(tmp_path)
        else:
            load_result = kg.load_bom_excel(tmp_path)
            
        os.unlink(tmp_path)
        
        raw_components = load_result.get("raw_components", [])
        
        # Get the running loop to pass to background task
        main_loop = asyncio.get_running_loop()
        
        # Start background analysis
        background_tasks.add_task(_run_bg_analysis, analysis_id, raw_components, main_loop)

        return {
            "success": True,
            "analysis_id": analysis_id,
            "message": "BOM loaded successfully. Analysis started.",
            "summary": load_result.get("summary", {})
        }
    except Exception as e:
        _analyses[analysis_id] = {"status": "error", "error": str(e)}
        return {"success": False, "message": f"Failed to upload: {str(e)}"}


@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Retrieve the results of a BOM analysis."""
    if analysis_id not in _analyses:
        raise HTTPException(status_code=404, detail="Analysis ID not found")
    return _analyses[analysis_id]


@app.post("/api/search-component")
async def api_search_component(req: SearchComponentRequest):
    """Analyze a single component on-demand."""
    try:
        enriched = analyze_single_component({
            "part_number": req.part_number,
            "description": req.description,
            "manufacturer": req.manufacturer,
            "package": req.package,
        })
        return {"success": True, "data": enriched}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/find-alternatives")
async def api_find_alternatives(req: FindAlternativesRequest):
    """Find alternatives for a single component with comparative specs."""
    try:
        alternatives = llm_find_alternatives(
            part_number=req.part_number,
            description=req.description,
            specs=req.specifications
        )
        return {"success": True, "alternatives": alternatives}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("Starting BOM Intelligence API v2 on http://localhost:8000")
    print("Docs at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
