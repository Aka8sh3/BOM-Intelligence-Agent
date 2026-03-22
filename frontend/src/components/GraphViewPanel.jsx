import React, { useEffect, useState, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

const GraphViewPanel = () => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const containerRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    // Measure container size for graph
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.offsetWidth,
        height: containerRef.current.offsetHeight
      });
    }
    
    // Fetch FalkorDB data
    const fetchGraph = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/graph');
        const result = await response.json();
        
        if (result.success) {
          // Process nodes to set colors based on types (matching Image 0 mockup)
          const processedNodes = result.data.nodes.map(node => {
            let color = '#3b82f6'; // Passives (blue)
            const lbl = node.label || '';
            const desc = (node.description || '').toLowerCase();
            
            if (lbl === 'Assembly' || desc.includes('board') || desc.includes('module')) color = '#3b82f6'; // Boards
            else if (desc.includes('ic') || desc.includes('microcontroller') || desc.includes('driver')) color = '#f43f5e'; // ICs (red/pink)
            else if (desc.includes('sensor')) color = '#22c55e'; // Sensors (green)
            else if (desc.includes('diode') || desc.includes('led')) color = '#d946ef'; // Others (purple)
            
            // Size based on label
            const val = lbl === 'Assembly' ? 20 : 10;
            
            return {
              ...node,
              color,
              val
            };
          });
          
          setGraphData({ nodes: processedNodes, links: result.data.links || [] });
        } else {
          setError(result.error);
        }
      } catch (err) {
        setError('Failed to connect to Knowledge Graph API. Is FalkorDB synced and backend running?');
      } finally {
        setLoading(false);
      }
    };
    
    fetchGraph();
  }, []);

  return (
    <div className="panel" style={{ padding: 0 }}>
      {loading && <div className="p-8 text-center text-secondary">Loading Semantic Graph from FalkorDB...</div>}
      {error && <div className="p-8 text-center text-status-critical">{error}</div>}
      
      {!loading && !error && (
        <div ref={containerRef} className="graph-container">
          <ForceGraph2D
            width={dimensions.width}
            height={dimensions.height}
            graphData={graphData}
            nodeLabel={node => `${node.name} (${node.label})\n${node.description || ''}`}
            nodeColor={node => node.color}
            nodeRelSize={4}
            linkColor={() => 'rgba(255, 255, 255, 0.2)'}
            linkWidth={1}
            linkDirectionalArrowLength={3.5}
            linkDirectionalArrowRelPos={1}
            linkLabel={link => `${link.label}${link.reasoning ? ': ' + link.reasoning : ''}`}
            backgroundColor="#0b0c10"
            d3AlphaDecay={0.02}
            d3VelocityDecay={0.3}
          />
          
          <div className="graph-legend">
             <div className="legend-item"><div className="legend-dot" style={{backgroundColor: '#3b82f6'}}></div> Boards & Passives</div>
             <div className="legend-item"><div className="legend-dot" style={{backgroundColor: '#f43f5e'}}></div> ICs & Controllers</div>
             <div className="legend-item"><div className="legend-dot" style={{backgroundColor: '#22c55e'}}></div> Sensors</div>
             <div className="legend-item"><div className="legend-dot" style={{backgroundColor: '#d946ef'}}></div> Connectors & Others</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GraphViewPanel;
