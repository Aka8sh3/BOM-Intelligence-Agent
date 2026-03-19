import React, { useState, useEffect, useRef } from 'react';
import { Download, IterationCcw, LayoutDashboard, List, DollarSign, Activity, Replace } from 'lucide-react';
import FileUploader from './FileUploader';
import OverviewPanel from './OverviewPanel';
import ComponentTable from './ComponentTable';
import PricingChart from './PricingChart';
import LifecyclePanel from './LifecyclePanel';
import AlternativesPanel from './AlternativesPanel';

const BomChangeAnalyser = () => {
  const [data, setData] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState({ percent: 0, current: 0, total: 0, part: '' });
  const [activeTab, setActiveTab] = useState('overview');
  const [error, setError] = useState(null);
  const wsRef = useRef(null);

  // Setup WebSocket for progress updates
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
          // Fetch final results
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
      setTimeout(connectWebSocket, 5000); // Reconnect
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
      // If success, we wait for WS 'complete' message to fetch results
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

  if (error) {
    return (
      <div className="app-container">
        <div className="topbar">
          <div className="topbar-title">⚡ <span>BOM Intelligence v2</span></div>
        </div>
        <div className="main-content" style={{ alignItems: 'center', justifyContent: 'center' }}>
          <div className="panel" style={{ maxWidth: '400px', textAlign: 'center' }}>
            <h3 className="text-status-critical mb-4">Analysis Error</h3>
            <p className="text-secondary mb-6">{error}</p>
            <button className="upload-btn mx-auto" onClick={() => setError(null)}>Try Again</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Topbar */}
      <div className="topbar">
        <div className="topbar-title">⚡ <span>BOM Intelligence v2</span></div>
        <div className="flex gap-4">
          <div className="text-xs text-muted flex items-center">
            PowerBI Dashboard Engine Active
          </div>
          {data && (
            <button className="flex items-center gap-2 px-4 py-1.5 bg-bg-panel hover:bg-bg-panel-hover border border-border-color rounded text-sm transition-colors text-text-primary" onClick={downloadJSON}>
              <Download size={16} className="text-accent-blue" /> Export Data
            </button>
          )}
          {data && (
            <button className="flex items-center gap-2 px-4 py-1.5 bg-bg-panel hover:bg-bg-panel-hover border border-border-color rounded text-sm transition-colors text-text-primary" onClick={() => setData(null)}>
              <IterationCcw size={16} className="text-status-medium" /> Reset
            </button>
          )}
        </div>
      </div>

      <div className="main-content">
        {!data ? (
          <FileUploader onUpload={handleUpload} isUploading={isUploading} progress={progress} />
        ) : (
          <>
            <div className="tabs-header">
              <button className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>
                <LayoutDashboard size={18} /> Overview
              </button>
              <button className={`tab-btn ${activeTab === 'table' ? 'active' : ''}`} onClick={() => setActiveTab('table')}>
                <List size={18} /> Component Data
              </button>
              <button className={`tab-btn ${activeTab === 'pricing' ? 'active' : ''}`} onClick={() => setActiveTab('pricing')}>
                <DollarSign size={18} /> Pricing & Coverage
              </button>
              <button className={`tab-btn ${activeTab === 'lifecycle' ? 'active' : ''}`} onClick={() => setActiveTab('lifecycle')}>
                <Activity size={18} /> Lifecycle Alerts
                {data.summary?.total_issues > 0 && (
                  <span className="badge badge-critical" style={{ padding: '0px 6px', fontSize: '10px' }}>{data.summary.total_issues}</span>
                )}
              </button>
              <button className={`tab-btn ${activeTab === 'alternatives' ? 'active' : ''}`} onClick={() => setActiveTab('alternatives')}>
                <Replace size={18} /> Alternatives
                {data.summary?.parts_with_alternatives > 0 && (
                  <span className="badge badge-low" style={{ padding: '0px 6px', fontSize: '10px' }}>{data.summary.parts_with_alternatives}</span>
                )}
              </button>
            </div>

            <div className="dashboard-view">
              {activeTab === 'overview' && <OverviewPanel data={data} />}
              {activeTab === 'table' && <ComponentTable data={data} />}
              {activeTab === 'pricing' && <PricingChart data={data} />}
              {activeTab === 'lifecycle' && <LifecyclePanel data={data} />}
              {activeTab === 'alternatives' && <AlternativesPanel data={data} />}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default BomChangeAnalyser;
