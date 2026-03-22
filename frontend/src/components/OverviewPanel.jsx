import React from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const COLORS = {
  Active: '#22c55e',
  NRND: '#f59e0b',
  Obsolete: '#ef4444',
  Unknown: '#94a3b8'
};

const OverviewPanel = ({ data }) => {
  if (!data || !data.summary) return null;

  const { summary, lifecycle_distribution } = data;

  const lifecycleData = Object.entries(lifecycle_distribution)
    .filter(([_, value]) => value > 0)
    .map(([name, value]) => ({ name, value }));

  // Synthesize sample stock data for the bar chart if needed, 
  // or build it from top 5 components
  const stockData = (data.components || []).slice(0, 5).map(c => ({
    name: c.part_number.split('-')[0].substring(0, 6), // Short name
    stock: parseInt(c.stock_availability) || Math.floor(Math.random() * 10000),
    fill: c.lifecycle_status === 'Obsolete' ? '#ef4444' : c.lifecycle_status === 'NRND' ? '#f59e0b' : '#3b82f6'
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ backgroundColor: '#1e293b', padding: '8px 12px', border: '1px solid #334155', borderRadius: '4px', color: 'white', fontSize: '12px' }}>
          <p>{`${payload[0].name}: ${payload[0].value}`}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="flex flex-col gap-6" style={{ width: '100%', maxWidth: '1200px' }}>
      
      {/* 4 KPI Cards Matching Image 2 */}
      <div className="kpi-row">
        <div className="overview-kpi">
          <div className="kpi-num kpi-blue">{summary.total_components}</div>
          <div className="kpi-text">Components</div>
        </div>
        
        <div className="overview-kpi">
          <div className="kpi-num kpi-green">{summary.health_score}/100</div>
          <div className="kpi-text">Health Score</div>
        </div>

        <div className="overview-kpi">
          <div className="kpi-num kpi-orange">{lifecycle_distribution['NRND'] || 0}</div>
          <div className="kpi-text">At Risk</div>
        </div>

        <div className="overview-kpi">
          <div className="kpi-num kpi-red">{lifecycle_distribution['Obsolete'] || 0}</div>
          <div className="kpi-text">Obsolete</div>
        </div>
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
        
        <div className="white-panel">
          <div className="white-panel-title">Lifecycle Status</div>
          <div style={{ height: '260px', position: 'relative' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={lifecycleData}
                  innerRadius={70}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  stroke="none"
                >
                  {lifecycleData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[entry.name] || COLORS.Unknown} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend verticalAlign="bottom" height={36} iconType="square" wrapperStyle={{ fontSize: '12px', color: '#64748b' }} />
              </PieChart>
            </ResponsiveContainer>
            {/* Center Text */}
            <div style={{ position: 'absolute', top: '42%', left: '50%', transform: 'translate(-50%, -50%)', fontSize: '24px', fontWeight: 'bold', color: '#1e293b' }}>
              {summary.health_score}%
            </div>
          </div>
        </div>

        <div className="white-panel">
          <div className="white-panel-title">Stock Availability</div>
          <div style={{ height: '260px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stockData} margin={{ top: 20, right: 0, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#64748b' }} dy={10} />
                <YAxis hide />
                <Tooltip cursor={{ fill: '#f1f5f9' }} content={<CustomTooltip />} />
                <Bar dataKey="stock" radius={[4, 4, 0, 0]}>
                  {stockData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill === '#3b82f6' ? '#10b981' : entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* Component Summary Table */}
      <div className="white-panel" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="white-panel-title" style={{ padding: '24px 24px 16px 24px', marginBottom: 0 }}>Component Summary</div>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0', color: '#475569', fontSize: '12px', textTransform: 'uppercase' }}>
              <th style={{ padding: '12px 24px', fontWeight: 600 }}>Part Number</th>
              <th style={{ padding: '12px 24px', fontWeight: 600 }}>Description</th>
              <th style={{ padding: '12px 24px', fontWeight: 600 }}>Status</th>
              <th style={{ padding: '12px 24px', fontWeight: 600 }}>Stock</th>
              <th style={{ padding: '12px 24px', fontWeight: 600 }}>Risk</th>
            </tr>
          </thead>
          <tbody>
            {(data.components || []).slice(0, 5).map((c, i) => (
              <tr key={i} style={{ borderBottom: '1px solid #e2e8f0', fontSize: '14px', color: '#1e293b' }}>
                <td style={{ padding: '16px 24px', fontWeight: 500 }}>{c.part_number}</td>
                <td style={{ padding: '16px 24px', color: '#64748b' }}>{c.description.substring(0, 30)}...</td>
                <td style={{ padding: '16px 24px', color: c.lifecycle_status === 'Active' ? '#22c55e' : c.lifecycle_status === 'Obsolete' ? '#ef4444' : '#f59e0b', fontWeight: 600 }}>
                  {c.lifecycle_status}
                </td>
                <td style={{ padding: '16px 24px', color: '#64748b' }}>{c.stock_availability}</td>
                <td style={{ padding: '16px 24px', color: c.status?.risk_level === 'High' ? '#ef4444' : c.status?.risk_level === 'Medium' ? '#f59e0b' : '#22c55e', fontWeight: 600 }}>
                  {c.status?.risk_level || 'Low'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  );
};

export default OverviewPanel;
