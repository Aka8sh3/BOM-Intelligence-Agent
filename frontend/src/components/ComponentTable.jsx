import React, { useState, useMemo } from 'react';
import { Search, ChevronDown, ChevronUp } from 'lucide-react';

const ComponentTable = ({ data }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: 'part_number', direction: 'asc' });

  if (!data || !data.components) return null;

  const sortedData = useMemo(() => {
    let sortableItems = [...data.components];
    
    // Search
    if (searchTerm) {
      sortableItems = sortableItems.filter(item => 
        (item.part_number && item.part_number.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (item.description && item.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (item.manufacturer && item.manufacturer.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Sort
    if (sortConfig !== null) {
      sortableItems.sort((a, b) => {
        let aVal = a[sortConfig.key] || '';
        let bVal = b[sortConfig.key] || '';
        if (sortConfig.key === 'alternatives_count') {
          aVal = a.alternatives ? a.alternatives.length : 0;
          bVal = b.alternatives ? b.alternatives.length : 0;
        }
        
        if (aVal < bVal) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (aVal > bVal) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableItems;
  }, [data.components, sortConfig, searchTerm]);

  const requestSort = (key) => {
    let direction = 'asc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const getSortIcon = (key) => {
    if (sortConfig.key !== key) return null;
    return sortConfig.direction === 'asc' ? <ChevronUp size={14} className="ml-1 inline" /> : <ChevronDown size={14} className="ml-1 inline" />;
  };

  const getLifecycleBadge = (status) => {
    switch (status) {
      case 'Active': return <span className="badge badge-low">Active</span>;
      case 'NRND': return <span className="badge badge-medium">NRND</span>;
      case 'EOL': return <span className="badge badge-high">EOL</span>;
      case 'Obsolete': return <span className="badge badge-critical">Obs</span>;
      default: return <span className="badge badge-neutral">{status}</span>;
    }
  };

  return (
    <div className="panel" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header" style={{ marginBottom: '16px' }}>
        <h3 className="panel-title">Component Master Data</h3>
        
        {/* Search Input */}
        <div style={{ position: 'relative', width: '300px' }}>
          <Search size={16} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--text-muted)' }} />
          <input 
            type="text" 
            placeholder="Search parts, description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ 
              width: '100%', padding: '8px 12px 8px 36px', 
              backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)', 
              borderRadius: '4px', color: 'var(--text-primary)' 
            }}
          />
        </div>
      </div>

      <div className="data-table-container" style={{ flex: 1, minHeight: '400px', maxHeight: '600px', overflowY: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th onClick={() => requestSort('part_number')} style={{cursor: 'pointer'}}>Part Number {getSortIcon('part_number')}</th>
              <th onClick={() => requestSort('manufacturer')} style={{cursor: 'pointer'}}>Mfr {getSortIcon('manufacturer')}</th>
              <th>Description</th>
              <th onClick={() => requestSort('lifecycle_status')} style={{cursor: 'pointer'}}>Lifecycle {getSortIcon('lifecycle_status')}</th>
              <th onClick={() => requestSort('availability')} style={{cursor: 'pointer'}}>Availability {getSortIcon('availability')}</th>
              <th onClick={() => requestSort('typical_price_usd')} style={{cursor: 'pointer'}}>Est. Price {getSortIcon('typical_price_usd')}</th>
              <th onClick={() => requestSort('alternatives_count')} style={{cursor: 'pointer', textAlign: 'center'}}>Alts {getSortIcon('alternatives_count')}</th>
            </tr>
          </thead>
          <tbody>
            {sortedData.length > 0 ? sortedData.map((item, idx) => (
              <tr key={idx}>
                <td style={{fontWeight: 600, color: 'var(--accent-blue)'}}>{item.part_number}</td>
                <td>{item.manufacturer}</td>
                <td style={{fontSize: '0.85rem', color: 'var(--text-secondary)'}}>{item.description}</td>
                <td>{getLifecycleBadge(item.lifecycle_status)}</td>
                <td>
                  <span style={{
                    color: item.availability === 'In Stock' ? 'var(--status-low)' : 
                           item.availability === 'Out of Stock' ? 'var(--status-critical)' : 'inherit'
                  }}>
                    {item.availability}
                  </span>
                </td>
                <td>{item.typical_price_usd ? (typeof item.typical_price_usd === 'number' ? `$${item.typical_price_usd.toFixed(4)}` : item.typical_price_usd) : '-'}</td>
                <td style={{textAlign: 'center'}}>
                  {item.alternatives && item.alternatives.length > 0 ? (
                    <span className="badge badge-low" style={{borderRadius: '4px'}}>{item.alternatives.length}</span>
                  ) : <span className="text-muted">-</span>}
                </td>
              </tr>
            )) : (
              <tr>
                <td colSpan="7" style={{textAlign: 'center', padding: '40px', color: 'var(--text-muted)'}}>
                  No components found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ComponentTable;
