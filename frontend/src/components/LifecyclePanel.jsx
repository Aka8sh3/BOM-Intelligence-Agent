import React from 'react';
import { AlertTriangle, Info, Clock, CheckCircle } from 'lucide-react';

const LifecyclePanel = ({ data }) => {
  if (!data || !data.issues) return null;

  const { issues } = data;

  const criticalIssues = issues.filter(i => i.severity === 'Critical');
  const highIssues = issues.filter(i => i.severity === 'High');

  const getIcon = (type) => {
    switch(type) {
      case 'End of Life': return <Clock size={20} className="text-status-critical" />;
      case 'PCN/PDN': return <Info size={20} className="text-status-medium" />;
      case 'Availability': return <AlertTriangle size={20} className="text-status-high" />;
      default: return <AlertTriangle size={20} />;
    }
  };

  const IssueCard = ({ issue }) => (
    <div style={{
      padding: '16px',
      backgroundColor: 'var(--bg-secondary)',
      borderLeft: `4px solid var(--status-${issue.severity.toLowerCase()})`,
      borderRadius: '0 8px 8px 0',
      marginBottom: '12px',
      display: 'flex',
      alignItems: 'flex-start',
      gap: '12px'
    }}>
      <div style={{marginTop: '2px'}}>
        {getIcon(issue.issue_type)}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h4 style={{ color: 'var(--accent-blue)', margin: 0 }}>{issue.part_number}</h4>
          <span className={`badge badge-${issue.severity.toLowerCase()}`}>{issue.issue_type}</span>
        </div>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>{issue.description}</p>
        
        {issue.has_alternatives ? (
          <div className="flex items-center gap-1 mt-2 text-xs text-status-low font-medium">
            <CheckCircle size={12} /> Alternates found in database
          </div>
        ) : (
          <div className="flex items-center gap-1 mt-2 text-xs text-status-critical font-medium">
            <AlertTriangle size={12} /> No immediate alternates found
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="grid-charts cols-2">
      <div className="panel" style={{ height: '100%', minHeight: '500px' }}>
        <div className="panel-header">
          <h3 className="panel-title flex items-center gap-2">
            <span className="badge badge-critical flex items-center gap-1" style={{fontSize: '0.9rem'}}>
              {criticalIssues.length}
            </span>
            Critical Action Required
          </h3>
        </div>
        <div style={{ overflowY: 'auto', flex: 1 }}>
          {criticalIssues.length > 0 ? (
            criticalIssues.map((issue, idx) => <IssueCard key={idx} issue={issue} />)
          ) : (
            <div className="text-center p-8 text-muted">
              <CheckCircle size={48} className="mx-auto mb-4 opacity-20" />
              <p>No critical lifecycle issues detected</p>
            </div>
          )}
        </div>
      </div>

      <div className="panel" style={{ height: '100%', minHeight: '500px' }}>
        <div className="panel-header">
          <h3 className="panel-title flex items-center gap-2">
            <span className="badge badge-high flex items-center gap-1" style={{fontSize: '0.9rem'}}>
              {highIssues.length}
            </span>
            High Priority Warnings
          </h3>
        </div>
        <div style={{ overflowY: 'auto', flex: 1 }}>
          {highIssues.length > 0 ? (
            highIssues.map((issue, idx) => <IssueCard key={idx} issue={issue} />)
          ) : (
            <div className="text-center p-8 text-muted">
              <CheckCircle size={48} className="mx-auto mb-4 opacity-20" />
              <p>No high priority warnings</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LifecyclePanel;
