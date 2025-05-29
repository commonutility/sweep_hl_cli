import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

const TestChart = () => {
  const chartContainerRef = useRef(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    console.log('Creating test chart...');
    
    const chart = createChart(chartContainerRef.current, {
      width: 600,
      height: 300,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#000000',
      },
    });

    const lineSeries = chart.addLineSeries();
    lineSeries.setData([
      { time: '2019-04-11', value: 80.01 },
      { time: '2019-04-12', value: 96.63 },
      { time: '2019-04-13', value: 76.64 },
      { time: '2019-04-14', value: 81.89 },
      { time: '2019-04-15', value: 74.43 },
      { time: '2019-04-16', value: 80.01 },
      { time: '2019-04-17', value: 96.63 },
      { time: '2019-04-18', value: 76.64 },
      { time: '2019-04-19', value: 81.89 },
      { time: '2019-04-20', value: 74.43 },
    ]);

    console.log('Test chart created successfully');

    return () => {
      console.log('Removing test chart');
      chart.remove();
    };
  }, []);

  return (
    <div style={{ padding: '20px' }}>
      <h2>Test Chart</h2>
      <div 
        ref={chartContainerRef} 
        style={{ 
          border: '1px solid #ccc',
          marginTop: '10px'
        }}
      />
    </div>
  );
};

export default TestChart; 