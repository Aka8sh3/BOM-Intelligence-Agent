import argparse
from falkordb import FalkorDB
from bom_kg_schema import BOMKnowledgeGraph, NodeType

def sync_bom_to_falkor(bom_file: str, host: str = "localhost", port: int = 6379, graph_name: str = "BOM_Intelligence"):
    print(f"Connecting to FalkorDB at {host}:{port}...")
    try:
        db = FalkorDB(host=host, port=port)
        graph = db.select_graph(graph_name)
    except Exception as e:
        print(f"Failed to connect to FalkorDB: {e}")
        return
        
    print(f"Loading BOM from '{bom_file}' into NetworkX memory...")
    bom_kg = BOMKnowledgeGraph()
    
    if bom_file.lower().endswith('.csv'):
        bom_kg.load_bom_csv(bom_file)
    elif bom_file.lower().endswith(('.xlsx', '.xls')):
        bom_kg.load_bom_excel(bom_file)
    else:
        print("Unsupported file format. Please use .csv or .xlsx")
        return
        
    print(f"Graph loaded: {bom_kg.G.number_of_nodes()} total nodes, {bom_kg.G.number_of_edges()} relationships")
    print("Synchronizing with FalkorDB...")
    
    # 1. Add Assembly Nodes
    assemblies = [node for node, data in bom_kg.G.nodes(data=True) if data.get('node_type') == NodeType.ASSEMBLY]
    for assembly in assemblies:
        safe_name = assembly.replace("'", "\\'")
        graph.query(f"MERGE (:Assembly {{name: '{safe_name}'}})")
    print(f"✅ Synced {len(assemblies)} Assemblies")
        
    # 2. Add Component Nodes
    components = [node for node, data in bom_kg.G.nodes(data=True) if data.get('node_type') == NodeType.COMPONENT]
    for comp in components:
        data = bom_kg.G.nodes[comp]
        safe_part = str(data.get('part_number', comp)).replace("'", "\\'")
        safe_desc = str(data.get('description', '')).replace("'", "\\'")
        safe_mfr = str(data.get('manufacturer', '')).replace("'", "\\'")
        
        query = f"""
        MERGE (:Component {{
            part_number: '{safe_part}', 
            description: '{safe_desc}', 
            manufacturer: '{safe_mfr}'
        }})
        """
        graph.query(query)
    print(f"✅ Synced {len(components)} Components")
    
    # 3. Add Edges (USED_IN relationships)
    edges_added = 0
    for u, v, data in bom_kg.G.edges(data=True):
        u_data = bom_kg.G.nodes[u]
        v_data = bom_kg.G.nodes[v]
        
        if u_data.get('node_type') == NodeType.COMPONENT and v_data.get('node_type') == NodeType.ASSEMBLY:
            safe_comp = str(u_data.get('part_number', u)).replace("'", "\\'")
            safe_assembly = v.replace("'", "\\'")
            
            query = f"""
            MATCH (c:Component {{part_number: '{safe_comp}'}}), (a:Assembly {{name: '{safe_assembly}'}})
            MERGE (c)-[:USED_IN]->(a)
            """
            graph.query(query)
            edges_added += 1
            
    # 4. LLM Semantic Relationship Discovery
    print("Asking AI to infer semantic relationships from the component list...")
    from llm_engine import llm_infer_bom_relationships
    
    # We pass the raw node dictionaries
    comp_list = []
    for comp in components:
        d = bom_kg.G.nodes[comp]
        if 'part_number' in d and 'description' in d:
             comp_list.append(d)
             
    semantic_edges_added = 0
    if comp_list:
        semantic_relationships = llm_infer_bom_relationships(comp_list)
        if semantic_relationships:
             print(f"AI discovered {len(semantic_relationships)} semantic relationships! Pushing to DB...")
             for rel in semantic_relationships:
                 src = str(rel.get("source_part", "")).replace("'", "\\'")
                 tgt = str(rel.get("target_part", "")).replace("'", "\\'")
                 verb = str(rel.get("relationship", "ASSOCIATED_WITH")).upper().replace(" ", "_").replace("-", "_")
                 reason = str(rel.get("reasoning", "")).replace("'", "\\'")
                 
                 if src and tgt and verb:
                     q = f"""
                     MATCH (s:Component {{part_number: '{src}'}}), (t:Component {{part_number: '{tgt}'}})
                     MERGE (s)-[:{verb} {{reasoning: '{reason}'}}]->(t)
                     """
                     try:
                         graph.query(q)
                         semantic_edges_added += 1
                     except Exception as e:
                         print(f"  Warning: Failed to execute {verb} query: {e}")
    
    print(f"✅ Synced {semantic_edges_added} advanced AI semantic edges")
    print("🚀 Synchronization complete! Open http://localhost:3000 to interact with your FalkorDB browser.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync BOM NetworkX Graph to FalkorDB for visual analytics.")
    parser.add_argument("bom_file", help="Path to your BOM CSV or Excel file")
    parser.add_argument("--host", default="localhost", help="FalkorDB host IP")
    parser.add_argument("--port", default=6379, type=int, help="FalkorDB port number")
    args = parser.parse_args()
    
    sync_bom_to_falkor(args.bom_file, args.host, args.port)
