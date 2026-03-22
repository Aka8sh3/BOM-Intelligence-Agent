import React from 'react';
import { LayoutDashboard, List, GitGraph, Replace, FileText } from 'lucide-react';

const Sidebar = ({ activeTab, setActiveTab }) => {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        BOM Intelligence
      </div>
      
      <div className="sidebar-nav">
        <button 
          className={`sidebar-item ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <LayoutDashboard size={20} /> Dashboard
        </button>
        
        <button 
          className={`sidebar-item ${activeTab === 'table' ? 'active' : ''}`}
          onClick={() => setActiveTab('table')}
        >
          <List size={20} /> Components
        </button>

        <button 
          className={`sidebar-item ${activeTab === 'graph' ? 'active' : ''}`}
          onClick={() => setActiveTab('graph')}
        >
          <GitGraph size={20} /> Graph View
        </button>

        <button 
          className={`sidebar-item ${activeTab === 'alternatives' ? 'active' : ''}`}
          onClick={() => setActiveTab('alternatives')}
        >
          <Replace size={20} /> Alternatives
        </button>

        <button 
          className={`sidebar-item ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          <FileText size={20} /> Reports
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
