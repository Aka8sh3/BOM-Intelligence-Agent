import React, { useState, useEffect, useRef } from 'react';
import { Download, IterationCcw } from 'lucide-react';
import FileUploader from './FileUploader';
import OverviewPanel from './OverviewPanel';
import ComponentTable from './ComponentTable';
import AlternativesPanel from './AlternativesPanel';
import GraphViewPanel from './GraphViewPanel';
import Sidebar from './Sidebar';

const BomChangeAnalyser = () => {
  const [data, setData] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState({ percent: 0, current: 0, total: 0, part: '' });
  const [activeTab, setActiveTab] = useState('overview');
  const [error, setError] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const connectWebSocket = () => {
    const ws = new WebSocket('ws://localhost:8000/ws/progress');
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'progress') {
          setProgress({
            percent: (msg.current / msg.total) * 100,
            current: msg.current,
            total: msg.total,
            part: msg.part_number
          });
        } else if (msg.type === 'complete') {
          fetchAnalysis(msg.analysis_id);
        } else if (msg.type === 'error') {
          setError(msg.error);
          setIsUploading(false);
        }
      } catch (err) {
        console.error('WebSocket message parsing error:', err);
      }
    };
    ws.onclose = () => {
      setTimeout(connectWebSocket, 5000);
    };
    wsRef.current = ws;
  };

  const fetchAnalysis = async (analysisId) => {
    try {
      const res = await fetch(`http://localhost:8000/api/analysis/${analysisId}`);
      if (res.ok) {
        const result = await res.json();
        if (result.status === 'complete' || result.status === 'Complete') {
          setData(result.result);
          setIsUploading(false);
        } else if (result.status === 'error') {
          setError(result.error);
          setIsUploading(false);
        }
      }
    } catch (err) {
      console.error(err);
      setError('Failed to fetch analysis results');
      setIsUploading(false);
    }
  };

  const handleUpload = async (file) => {
    setIsUploading(true);
    setError(null);
    setProgress({ percent: 0, current: 0, total: 0, part: 'Initializing...' });
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await fetch('http://localhost:8000/api/upload-bom', {
        method: 'POST',
        body: formData,
      });
      const result = await res.json();
      if (!result.success) {
        setError(result.message);
        setIsUploading(false);
      }
    } catch (err) {
      console.error(err);
      setError('Upload failed. Is the backend running?');
      setIsUploading(false);
    }
  };

  const downloadJSON = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bom-analysis-export-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getPageTitle = () => {
    switch (activeTab) {
      case 'overview': return 'Dashboard Overview';
      case 'table': return 'Component Data';
      case 'graph': return 'Knowledge Graph';
      case 'alternatives': return 'Alternative Components';
      case 'reports': return 'Reports & Exports';
      default: return 'BOM Intelligence';
    }
  };

  return (
    <div className="app-layout">
      {/* Sidebar Navigation */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <div className="main-area">
        <div className="topbar">
          <div className="page-title">
            {activeTab === 'graph' && <span className="text-muted">BOM Intelligence Platform &mdash; </span>}
            {getPageTitle()}
            {activeTab === 'graph' && <span className="text-muted text-sm" style={{marginLeft: 'auto', justifySelf: 'flex-end', fontSize: '14px', fontWeight: '400'}}>26 Nodes &bull; 46 Edges</span>}
          </div>
          
          <div className="flex gap-4">
            {data && (
              <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors font-medium border-0" onClick={downloadJSON}>
                <Download size={16} /> Export Data
              </button>
            )}
            {data && (
              <button className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 rounded text-sm transition-colors font-medium" onClick={() => setData(null)}>
                <IterationCcw size={16} /> Reset
              </button>
            )}
          </div>
        </div>

        <div className="content-wrapper">
          {error ? (
            <div className="panel" style={{ maxWidth: '400px', textAlign: 'center', margin: '100px auto' }}>
              <h3 className="text-status-critical mb-4">Analysis Error</h3>
              <p className="text-secondary mb-6">{error}</p>
              <button className="upload-btn mx-auto" onClick={() => setError(null)}>Try Again</button>
            </div>
          ) : !data ? (
             activeTab === 'graph' ? <GraphViewPanel /> : <FileUploader onUpload={handleUpload} isUploading={isUploading} progress={progress} />
          ) : (
            <>
              {activeTab === 'overview' && <OverviewPanel data={data} />}
              {activeTab === 'table' && <ComponentTable data={data} />}
              {activeTab === 'graph' && <GraphViewPanel data={data} />}
              {activeTab === 'alternatives' && <AlternativesPanel data={data} />}
              {activeTab === 'reports' && (
                <div className="panel">
                  <h3 className="text-lg font-bold mb-4">Export Reports</h3>
                  <button onClick={downloadJSON} className="upload-btn w-max">Download Full JSON Payload</button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default BomChangeAnalyser;
