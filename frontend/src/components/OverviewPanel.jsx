import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, Legend } from 'recharts';
import { Target, AlertTriangle, CheckCircle, PackageSearch } from 'lucide-react';

const COLORS = {
  Active: '#22c55e',
  NRND: '#eab308',
  Obsolete: '#ef4444',
  EOL: '#f97316',
  Unknown: '#6b7280',
  'In Stock': '#3b82f6',
  'Limited': '#f6c85f',
  'Out of Stock': '#ef4444'
};

const OverviewPanel = ({ data }) => {
  if (!data || !data.summary) return null;

  const { summary, lifecycle_distribution, availability_distribution } = data;

  // Format data for Recharts Pie
  const lifecycleData = Object.entries(lifecycle_distribution)
    .filter(([_, value]) => value > 0)
    .map(([name, value]) => ({ name, value }));

  const availabilityData = Object.entries(availability_distribution)
    .filter(([_, value]) => value > 0)
    .map(([name, value]) => ({ name, value }));

  return (
    <div className="dashboard-content">
      {/* KPI Cards */}
      <div className="grid-overview" style={{ marginBottom: '16px' }}>
        <div className="kpi-card kpi-blue">
          <div className="kpi-label flex items-center gap-2"><PackageSearch size={16}/> Total Components</div>
          <div className="kpi-value">{summary.total_components}</div>
          <div className="text-sm mt-2 text-secondary">{summary.unique_parts} unique MPNs</div>
        </div>
        
        <div className={`kpi-card ${summary.health_score > 80 ? 'kpi-green' : summary.health_score > 50 ? 'kpi-orange' : 'kpi-red'}`}>
          <div className="kpi-label flex items-center gap-2"><Target size={16}/> Health Score</div>
          <div className="kpi-value">{summary.health_score}/100</div>
          <div className="text-sm mt-2 text-secondary">Based on lifecycle & availability</div>
        </div>

        <div className={`kpi-card ${summary.overall_risk === 'Critical' ? 'kpi-red' : summary.overall_risk === 'High' ? 'kpi-orange' : summary.overall_risk === 'Medium' ? 'kpi-purple' : 'kpi-green'}`}>
          <div className="kpi-label flex items-center gap-2"><AlertTriangle size={16}/> Overall Risk</div>
          <div className="kpi-value">{summary.overall_risk}</div>
          <div className="text-sm mt-2 text-secondary">{summary.total_issues} issues detected</div>
        </div>

        <div className="kpi-card kpi-purple">
          <div className="kpi-label flex items-center gap-2"><CheckCircle size={16}/> Parts with Alternates</div>
          <div className="kpi-value">{summary.parts_with_alternatives}</div>
          <div className="text-sm mt-2 text-secondary">{summary.total_alternatives_found} total replacements found</div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid-charts">
        <div className="panel" style={{ height: '350px' }}>
          <div className="panel-header">
            <h3 className="panel-title">Lifecycle Distribution</h3>
          </div>
          <div style={{ flex: 1, minHeight: 0 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={lifecycleData}
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {lifecycleData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[entry.name] || COLORS.Unknown} />
                  ))}
                </Pie>
                <RechartsTooltip contentStyle={{ backgroundColor: '#222633', border: '1px solid #3a4055', borderRadius: '8px' }} />
                <Legend verticalAlign="bottom" height={36}/>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel" style={{ height: '350px' }}>
          <div className="panel-header">
            <h3 className="panel-title">Stock Availability</h3>
          </div>
          <div style={{ flex: 1, minHeight: 0 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={availabilityData}
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {availabilityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[entry.name] || COLORS.Unknown} />
                  ))}
                </Pie>
                <RechartsTooltip contentStyle={{ backgroundColor: '#222633', border: '1px solid #3a4055', borderRadius: '8px' }} />
                <Legend verticalAlign="bottom" height={36}/>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OverviewPanel;
