import React, { useState, useEffect } from 'react';
import './MultiPanelAsset.css';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const MultiPanelAsset = ({ symbols = ['BTC', 'ETH', 'SOL', 'ARB'], quoteAsset = 'USD', interval: initialInterval = '1h' }) => {
  const [assetsData, setAssetsData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentInterval, setCurrentInterval] = useState(initialInterval);

  // Interval options matching the main system
  const intervals = {
    '5m': { label: '5 min', days: 0.25 },  // 6 hours of data for 5m
    '1h': { label: '1 hour', days: 7 },    // 7 days of data for 1h
    '1d': { label: '1 day', days: 180 }    // 180 days of data for 1d
  };

  useEffect(() => {
    // Handle interval updates
    const handleIntervalUpdate = (event) => {
      setCurrentInterval(event.detail);
    };
    
    window.addEventListener('updateMultiPanelInterval', handleIntervalUpdate);
    
    return () => {
      window.removeEventListener('updateMultiPanelInterval', handleIntervalUpdate);
    };
  }, []);

  useEffect(() => {
    fetchAllAssetsData();
    // Update frequency based on interval
    const updateFrequency = currentInterval === '5m' ? 10000 : 30000; // 10s for 5m, 30s for others
    const intervalId = setInterval(fetchAllAssetsData, updateFrequency);
    return () => clearInterval(intervalId);
  }, [symbols, quoteAsset, currentInterval]);

  const fetchAllAssetsData = async () => {
    try {
      const promises = symbols.map(symbol => fetchAssetData(symbol));
      const results = await Promise.all(promises);
      
      const newAssetsData = {};
      results.forEach((data, index) => {
        if (data) {
          newAssetsData[symbols[index]] = data;
        }
      });
      
      setAssetsData(newAssetsData);
      setError(null);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching assets data:', err);
      setError('Failed to load asset data');
      setLoading(false);
    }
  };

  const fetchAssetData = async (symbol) => {
    try {
      // Fetch current price
      const currentResponse = await fetch(`http://localhost:8000/api/assets/${symbol}/current?quote=${quoteAsset}`);
      if (!currentResponse.ok) throw new Error(`Failed to fetch current price for ${symbol}`);
      const currentData = await currentResponse.json();

      // Fetch price history with interval parameter
      const days = intervals[currentInterval].days;
      const historyResponse = await fetch(
        `http://localhost:8000/api/assets/${symbol}/price-history?days=${days}&quote=${quoteAsset}&interval=${currentInterval}`
      );
      if (!historyResponse.ok) throw new Error(`Failed to fetch price history for ${symbol}`);
      const historyData = await historyResponse.json();

      return {
        current: currentData,
        history: historyData.data || []
      };
    } catch (err) {
      console.error(`Error fetching data for ${symbol}:`, err);
      return null;
    }
  };

  const formatPrice = (price) => {
    if (!price || price === 0) return '$0.00';
    if (price >= 10000) return `$${(price / 1000).toFixed(0)}K`;
    if (price >= 1000) return `$${(price / 1000).toFixed(1)}K`;
    if (price >= 100) return `$${price.toFixed(0)}`;
    if (price >= 1) return `$${price.toFixed(2)}`;
    if (price >= 0.01) return `$${price.toFixed(4)}`;
    return `$${price.toFixed(6)}`;
  };

  const formatPercent = (percent) => {
    const formatted = Math.abs(percent).toFixed(2);
    return percent >= 0 ? `+${formatted}%` : `-${formatted}%`;
  };

  const formatXAxis = (timestamp) => {
    const date = new Date(timestamp);
    const hours = date.getHours();
    const minutes = date.getMinutes();
    
    switch (currentInterval) {
      case '5m':
      case '1h':
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
      case '1d':
        return date.toLocaleDateString('en-US', { weekday: 'short' });
      default:
        return date.toLocaleDateString();
    }
  };

  const renderAssetPanel = (symbol) => {
    const data = assetsData[symbol];
    if (!data) return null;

    const { current, history } = data;
    const priceChange = current.price_change_percent || 0;
    const isPositive = priceChange >= 0;

    return (
      <div className="asset-panel" key={symbol}>
        <div className="asset-header">
          <div className="asset-title">
            <h3>{symbol}/{quoteAsset}</h3>
            <span className={`price-change ${isPositive ? 'positive' : 'negative'}`}>
              {formatPercent(priceChange)}
            </span>
          </div>
          <div className="asset-price">
            <span className="current-price">{formatPrice(current.price)}</span>
          </div>
        </div>
        
        <div className="chart-container">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={formatXAxis}
                stroke="#666"
                fontSize={10}
              />
              <YAxis 
                domain={['dataMin', 'dataMax']}
                tickFormatter={(value) => formatPrice(value).replace('$', '')}
                stroke="#666"
                fontSize={10}
                width={50}
              />
              <Tooltip 
                formatter={(value) => formatPrice(value)}
                labelFormatter={(timestamp) => new Date(timestamp).toLocaleString()}
                contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
              />
              <Line 
                type="monotone" 
                dataKey="price" 
                stroke={isPositive ? '#00ff88' : '#ff3366'}
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        
        <div className="asset-stats">
          <div className="stat">
            <span className="stat-label">24h Vol</span>
            <span className="stat-value">{formatPrice(current.volume_24h || 0)}</span>
          </div>
          <div className="stat">
            <span className="stat-label">24h High</span>
            <span className="stat-value">{formatPrice(current.high_24h || current.price)}</span>
          </div>
          <div className="stat">
            <span className="stat-label">24h Low</span>
            <span className="stat-value">{formatPrice(current.low_24h || current.price)}</span>
          </div>
        </div>
      </div>
    );
  };

  if (loading && Object.keys(assetsData).length === 0) {
    return (
      <div className="multipanel-asset-container">
        <div className="loading-message">Loading asset data...</div>
      </div>
    );
  }

  if (error && Object.keys(assetsData).length === 0) {
    return (
      <div className="multipanel-asset-container">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  return (
    <div className="multipanel-asset-container">
      <div className="multipanel-header">
        <h2>Multi-Asset View</h2>
        <div className="time-range-selector">
          {Object.entries(intervals).map(([key, value]) => (
            <button
              key={key}
              className={`time-range-btn ${currentInterval === key ? 'active' : ''}`}
              onClick={() => window.dispatchEvent(new CustomEvent('updateMultiPanelInterval', { detail: key }))}
            >
              {value.label}
            </button>
          ))}
        </div>
      </div>
      
      <div className="assets-grid">
        {symbols.map(symbol => renderAssetPanel(symbol))}
      </div>
    </div>
  );
};

export default MultiPanelAsset; 