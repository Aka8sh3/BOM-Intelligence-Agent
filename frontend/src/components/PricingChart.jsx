import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, LabelList, Cell } from 'recharts';

const PricingChart = ({ data }) => {
  if (!data || !data.components) return null;

  // Aggregate average pricing by vendor
  const vendorData = useMemo(() => {
    const vendorMap = {};
    
    data.components.forEach(comp => {
      if (comp.vendors) {
        comp.vendors.forEach(v => {
          if (!v.name) return;
          if (!vendorMap[v.name]) {
            vendorMap[v.name] = { name: v.name, totalPrice: 0, count: 0, available: 0 };
          }
          if (typeof v.price_usd === 'number') {
            vendorMap[v.name].totalPrice += v.price_usd;
            vendorMap[v.name].count += 1;
          }
          if (v.stock === 'In Stock' || v.stock === 'Limited') {
             vendorMap[v.name].available += 1;
          }
        });
      }
    });

    return Object.values(vendorMap).map(v => ({
      name: v.name,
      avgPrice: v.count > 0 ? (v.totalPrice / v.count).toFixed(4) : 0,
      availabilityPct: Math.round((v.available / data.summary.total_components) * 100)
    })).sort((a, b) => b.availabilityPct - a.availabilityPct);
  }, [data]);


  return (
    <div className="grid-charts cols-2">
      <div className="panel" style={{ height: '400px' }}>
        <div className="panel-header">
          <h3 className="panel-title">Vendor Average Pricing (USD)</h3>
        </div>
        <div style={{ flex: 1, minHeight: 0 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={vendorData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#2e3344" horizontal={true} vertical={false} />
              <XAxis type="number" stroke="#6b7280" tick={{fill: '#a0a6b5'}} tickFormatter={(v) => `$${v}`}/>
              <YAxis dataKey="name" type="category" stroke="#6b7280" tick={{fill: '#a0a6b5'}} width={80} />
              <RechartsTooltip 
                contentStyle={{ backgroundColor: '#222633', border: '1px solid #3a4055', borderRadius: '8px' }}
                formatter={(val) => [`$${val}`, 'Avg Price']}
              />
              <Bar dataKey="avgPrice" fill="var(--accent-cyan)" radius={[0, 4, 4, 0]}>
                <LabelList dataKey="avgPrice" position="right" fill="#f0f0f5" formatter={(v) => `$${v}`} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="panel" style={{ height: '400px' }}>
        <div className="panel-header">
          <h3 className="panel-title">Vendor BOM Coverage (%)</h3>
        </div>
        <div style={{ flex: 1, minHeight: 0 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={vendorData}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#2e3344" vertical={false} />
              <XAxis dataKey="name" stroke="#6b7280" tick={{fill: '#a0a6b5'}} />
              <YAxis tickFormatter={(tick) => `${tick}%`} stroke="#6b7280" tick={{fill: '#a0a6b5'}} domain={[0, 100]} />
              <RechartsTooltip 
                contentStyle={{ backgroundColor: '#222633', border: '1px solid #3a4055', borderRadius: '8px' }}
                formatter={(val) => [`${val}%`, 'Coverage']}
              />
              <Bar dataKey="availabilityPct" radius={[4, 4, 0, 0]}>
                {vendorData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.availabilityPct > 80 ? 'var(--status-low)' : entry.availabilityPct > 50 ? 'var(--status-medium)' : 'var(--status-high)'} />
                ))}
                <LabelList dataKey="availabilityPct" position="top" fill="#f0f0f5" formatter={(v) => `${v}%`} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default PricingChart;
