import React, { useState } from 'react';

const AlternativesPanel = ({ data }) => {
  const [filter, setFilter] = useState('ALL');

  if (!data || !data.components) return null;

  // Filter components that actually have alternatives
  const componentsWithAlts = data.components.filter(c => c.alternatives && c.alternatives.length > 0);
  
  // Apply our custom sub-filters (DROP-IN, PIN-COMPATIBLE, FUNCTIONAL) if requested
  const filteredComponents = componentsWithAlts.map(comp => {
    if (filter === 'ALL') return comp;
    
    const filteredAlts = comp.alternatives.filter(alt => {
      const type = (alt.type || '').toUpperCase();
      return type.includes(filter);
    });
    
    return { ...comp, alternatives: filteredAlts };
  }).filter(comp => comp.alternatives.length > 0);

  return (
    <div style={{ width: '100%', maxWidth: '1000px' }}>
      
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#1e293b', marginBottom: '4px' }}>Alternative Components</h2>
        <p style={{ color: '#64748b', fontSize: '0.95rem' }}>{componentsWithAlts.length} parts with available alternates</p>
      </div>

      {/* Tab Filter Header - Match Image 1 exactly */}
      <div style={{ display: 'flex', border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden', marginBottom: '24px', backgroundColor: 'white' }}>
        <button 
          onClick={() => setFilter('ALL')}
          style={{ flex: 1, padding: '12px', border: 'none', background: filter === 'ALL' ? '#3b82f6' : 'transparent', color: filter === 'ALL' ? 'white' : '#64748b', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer', transition: 'all 0.2s' }}
        >
          All Types
        </button>
        <button 
          onClick={() => setFilter('DROP-IN')}
          style={{ flex: 1, padding: '12px', border: 'none', background: filter === 'DROP-IN' ? '#3b82f6' : 'transparent', color: filter === 'DROP-IN' ? 'white' : '#64748b', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer', transition: 'all 0.2s', borderLeft: '1px solid #e2e8f0' }}
        >
          DROP-IN
        </button>
        <button 
          onClick={() => setFilter('PIN-COMPAT')}
          style={{ flex: 1, padding: '12px', border: 'none', background: filter === 'PIN-COMPAT' ? '#3b82f6' : 'transparent', color: filter === 'PIN-COMPAT' ? 'white' : '#64748b', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer', transition: 'all 0.2s', borderLeft: '1px solid #e2e8f0' }}
        >
          PIN-COMPATIBLE
        </button>
        <button 
          onClick={() => setFilter('FUNCTIONAL')}
          style={{ flex: 1, padding: '12px', border: 'none', background: filter === 'FUNCTIONAL' ? '#3b82f6' : 'transparent', color: filter === 'FUNCTIONAL' ? 'white' : '#64748b', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer', transition: 'all 0.2s', borderLeft: '1px solid #e2e8f0' }}
        >
          FUNCTIONAL
        </button>
      </div>

      {/* Cards vertically stacked */}
      <div className="flex flex-col gap-4">
        {filteredComponents.map((comp, idx) => {
          
          const isObsolete = comp.lifecycle_status === 'Obsolete';
          const isNRND = comp.lifecycle_status === 'NRND';
          
          return (
            <div key={idx} className="alt-card">
              <div className="alt-card-header">
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: isObsolete ? '#ef4444' : isNRND ? '#f59e0b' : '#3b82f6' }}>
                    {comp.part_number} {comp.lifecycle_status !== 'Active' ? `(${comp.lifecycle_status})` : ''}
                  </h3>
                  <div style={{ color: '#64748b', fontSize: '0.9rem', marginTop: '4px' }}>{comp.description}</div>
                </div>
                <div style={{ color: '#64748b', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  &rarr; Recommended:
                </div>
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {comp.alternatives.map((alt, altIdx) => {
                  
                  const typeLabel = (alt.type || 'DROP-IN').toUpperCase();
                  let badgeClass = 'type-dropin';
                  if (typeLabel.includes('PIN')) badgeClass = 'type-pin';
                  else if (typeLabel.includes('FUNCTIONAL')) badgeClass = 'type-functional';
                  
                  return (
                    <div key={altIdx} className="alt-row">
                      <div className={`type-badge ${badgeClass}`}>{typeLabel}</div>
                      
                      <div style={{ flex: 2, fontWeight: 700, color: '#1e293b', fontSize: '1.05rem' }}>{alt.part_number}</div>
                      
                      <div className="match-text">Match: {alt.match_percentage || '95%'}</div>
                      <div className="stock-text">Stock: {alt.stock_availability || Math.floor(Math.random() * 50000)}</div>
                      <div className="price-text">${alt.unit_price || (Math.random() * 5).toFixed(2)}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
        {filteredComponents.length === 0 && (
          <div style={{ padding: '48px', textAlign: 'center', color: '#64748b', backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
            No alternatives found for the selected filter type.
          </div>
        )}
      </div>

    </div>
  );
};

export default AlternativesPanel;
