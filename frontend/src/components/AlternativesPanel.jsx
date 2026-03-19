import React, { useState } from 'react';
import { ArrowLeftRight, CheckCircle, AlertCircle, Info, Star } from 'lucide-react';

const AlternativesPanel = ({ data }) => {
  if (!data || !data.components) return null;

  const componentsWithAlts = data.components.filter(c => c.alternatives && c.alternatives.length > 0);
  
  const [selectedComp, setSelectedComp] = useState(componentsWithAlts.length > 0 ? componentsWithAlts[0] : null);

  if (componentsWithAlts.length === 0) {
    return (
      <div className="panel" style={{ height: '500px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="text-center text-muted">
          <Info size={48} className="mx-auto mb-4 opacity-20" />
          <p>No alternatives found in the current BOM analysis.</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', gap: '16px', height: 'calc(100vh - 160px)' }}>
      {/* Left sidebar - Component List */}
      <div className="panel" style={{ width: '300px', display: 'flex', flexDirection: 'column', padding: '0' }}>
        <div className="panel-header" style={{ padding: '20px 20px 0 20px' }}>
          <h3 className="panel-title text-sm">Parts w/ Alternates ({componentsWithAlts.length})</h3>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '10px 0' }}>
          {componentsWithAlts.map((comp, idx) => (
            <div 
              key={idx}
              onClick={() => setSelectedComp(comp)}
              style={{
                padding: '12px 20px',
                cursor: 'pointer',
                backgroundColor: selectedComp?.part_number === comp.part_number ? 'var(--bg-panel-hover)' : 'transparent',
                borderLeft: selectedComp?.part_number === comp.part_number ? '3px solid var(--accent-blue)' : '3px solid transparent',
              }}
            >
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9rem' }}>{comp.part_number}</div>
              <div className="text-xs text-muted mt-1 truncate">{comp.description}</div>
              <div className="flex items-center gap-2 mt-2">
                <span className="badge badge-low text-xs" style={{ padding: '2px 6px' }}>{comp.alternatives.length} alts</span>
                {comp.lifecycle_status === 'Obsolete' && <span className="badge badge-critical text-xs" style={{ padding: '2px 6px' }}>Obs</span>}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right side - Comparison */}
      {selectedComp && (
        <div className="panel" style={{ flex: 1, overflowY: 'auto' }}>
          <div className="flex items-center justify-between mb-6 pb-6 border-b border-border-color">
            <div>
              <h2 className="text-xl font-bold flex items-center gap-2">
                <AlertCircle className={selectedComp.lifecycle_status === 'Obsolete' ? 'text-status-critical' : 'text-status-medium'} />
                {selectedComp.part_number}
              </h2>
              <p className="text-secondary mt-1">{selectedComp.description}</p>
              <div className="flex items-center gap-3 mt-3 text-sm">
                <span><span className="text-muted">Mfr:</span> {selectedComp.manufacturer}</span>
                <span><span className="text-muted">Package:</span> {selectedComp.specifications?.package || 'Unknown'}</span>
                <span><span className="text-muted">Lifecycle:</span> <span className={`text-status-${selectedComp.lifecycle_status === 'Obsolete' ? 'critical' : 'low'}`}>{selectedComp.lifecycle_status}</span></span>
              </div>
            </div>
          </div>

          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <ArrowLeftRight size={18} className="text-accent-blue" /> Recommended Replacements
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {selectedComp.alternatives.map((alt, idx) => (
              <div key={idx} style={{ 
                border: '1px solid var(--border-color)', 
                borderRadius: '8px', 
                padding: '20px',
                backgroundColor: 'var(--bg-secondary)',
                position: 'relative',
                overflow: 'hidden'
              }}>
                {idx === 0 && (
                  <div style={{ position: 'absolute', top: 0, right: 0, background: 'var(--accent-blue)', color: 'white', fontSize: '0.7rem', fontWeight: 600, padding: '4px 12px', borderBottomLeftRadius: '8px' }}>
                    TOP MATCH
                  </div>
                )}
                
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-accent-cyan flex items-center gap-2">
                      {alt.part_number}
                      {alt.compatibility === 'Drop-in' && <CheckCircle size={14} className="text-status-low" />}
                    </h4>
                    <p className="text-sm text-secondary mt-1">{alt.description || 'No description'}</p>
                    <p className="text-xs text-muted mt-1">Mfr: {alt.manufacturer || 'Unknown'} | Est. Price: {alt.estimated_price_usd ? `$${alt.estimated_price_usd}` : 'N/A'}</p>
                  </div>
                  <div className="text-right">
                    <span className={`badge ${alt.compatibility === 'Drop-in' ? 'badge-low' : alt.compatibility === 'Pin-Compatible' ? 'badge-medium' : 'badge-high'}`}>
                      {alt.compatibility || 'Functional'}
                    </span>
                    {alt.confidence_score && (
                      <div className="text-xs text-muted mt-2 flex items-center justify-end gap-1">
                        <Star size={12} className="text-accent-gold" /> {Math.round(alt.confidence_score * 100)}% Match
                      </div>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mt-6 pt-4 border-t border-border-light">
                  <div>
                    <h5 className="text-xs font-semibold text-muted uppercase tracking-wider mb-2">Advantages</h5>
                    <ul className="text-sm text-status-low flex flex-col gap-1">
                      {alt.advantages && alt.advantages.length > 0 ? alt.advantages.map((adv, i) => (
                        <li key={i} className="flex items-start gap-2"><CheckCircle size={14} className="mt-0.5 shrink-0" /> {adv}</li>
                      )) : <li className="text-muted italic">None specified</li>}
                    </ul>
                  </div>
                  <div>
                    <h5 className="text-xs font-semibold text-muted uppercase tracking-wider mb-2">Disadvantages / Differences</h5>
                    <ul className="text-sm text-status-high flex flex-col gap-1">
                      {alt.disadvantages && alt.disadvantages.length > 0 ? alt.disadvantages.map((dis, i) => (
                        <li key={i} className="flex items-start gap-2"><AlertCircle size={14} className="mt-0.5 shrink-0" /> {dis}</li>
                      )) : (alt.key_differences ? <li className="flex items-start gap-2"><AlertCircle size={14} className="mt-0.5 shrink-0" /> {alt.key_differences}</li> : <li className="text-muted italic">None known</li>)}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AlternativesPanel;
