import React, { useEffect, useRef } from 'react';
import { createChart, LineSeries } from 'lightweight-charts';

const TestChart = () => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    console.log('TestChart: Container element:', chartContainerRef.current);
    console.log('TestChart: Container dimensions:', {
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      offsetWidth: chartContainerRef.current.offsetWidth,
      offsetHeight: chartContainerRef.current.offsetHeight
    });

    // Create chart with explicit dimensions
    const chart = createChart(chartContainerRef.current, {
      width: 600,
      height: 400,
      layout: {
        background: { color: '#1a1a1a' },
        textColor: '#d1d4dc',
      },
      watermark: {
        visible: false,
      },
    });

    chartRef.current = chart;

    // Add a simple line series with test data - v5 syntax
    const lineSeries = chart.addSeries(LineSeries, {
      color: '#00ff88',
      lineWidth: 2,
    });

    // Generate test data
    const testData = [];
    const baseTime = Math.floor(Date.now() / 1000) - 100 * 60; // 100 minutes ago
    for (let i = 0; i < 100; i++) {
      testData.push({
        time: baseTime + i * 60,
        value: 50000 + Math.sin(i / 10) * 1000 + Math.random() * 500
      });
    }

    console.log('TestChart: Setting test data:', testData.slice(0, 5));
    lineSeries.setData(testData);

    // Fit content
    chart.timeScale().fitContent();

    return () => {
      chart.remove();
    };
  }, []);

  return (
    <div style={{ padding: '20px', backgroundColor: '#0a0a0a', height: '100vh' }}>
      <h2 style={{ color: '#fff', marginBottom: '20px' }}>TradingView Chart Test</h2>
      <div 
        ref={chartContainerRef} 
        style={{ 
          width: '600px', 
          height: '400px', 
          backgroundColor: '#1a1a1a',
          border: '1px solid #333'
        }}
      />
      <p style={{ color: '#888', marginTop: '20px' }}>
        If you see a chart above with a green line, TradingView is working correctly.
      </p>
    </div>
  );
};

export default TestChart; 