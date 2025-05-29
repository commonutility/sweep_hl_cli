import React, { useEffect, useRef, useState } from 'react';
import { 
  createChart, 
  CrosshairMode, 
  LineStyle,
  CandlestickSeries,
  LineSeries,
  HistogramSeries 
} from 'lightweight-charts';
import './PriceChart.css';

const PriceChart = ({ 
  priceData, 
  isLiveMode = false, 
  userTrades = [],
  symbol = 'BTC',
  quoteAsset = 'USD',
  height = 400 
}) => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candleSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const lineSeriesRef = useRef(null);
  const markersRef = useRef([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: height,
      layout: {
        background: { color: '#0a0a0a' },
        textColor: '#d1d4dc',
      },
      watermark: {
        visible: false,
      },
      grid: {
        vertLines: { color: '#1e1e1e' },
        horzLines: { color: '#1e1e1e' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          width: 1,
          color: '#758696',
          style: LineStyle.Solid,
          labelBackgroundColor: '#2b2b43',
        },
        horzLine: {
          width: 1,
          color: '#758696',
          style: LineStyle.Solid,
          labelBackgroundColor: '#2b2b43',
        },
      },
      rightPriceScale: {
        borderColor: '#2b2b43',
        scaleMargins: {
          top: 0.1,
          bottom: 0.2,
        },
      },
      timeScale: {
        borderColor: '#2b2b43',
        timeVisible: true,
        secondsVisible: isLiveMode,
        tickMarkFormatter: (time, tickMarkType, locale) => {
          const date = new Date(time * 1000);
          
          if (isLiveMode) {
            // For live mode, show time
            return date.toLocaleTimeString(locale, { 
              hour: '2-digit', 
              minute: '2-digit',
              second: '2-digit'
            });
          } else {
            // For historical data, show date
            return date.toLocaleDateString(locale, { 
              month: 'short', 
              day: 'numeric' 
            });
          }
        },
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: false,
      },
      handleScale: {
        mouseWheel: true,
        pinch: true,
        axisPressedMouseMove: true,
      },
    });

    let mainSeries;
    
    if (isLiveMode) {
      // For live mode, use line series
      mainSeries = chart.addSeries(LineSeries, {
        color: '#00ff88',
        lineWidth: 2,
        priceScaleId: 'right',
        lastValueVisible: true,
        priceLineVisible: true,
      });
      lineSeriesRef.current = mainSeries;
    } else {
      // For historical data, use candlestick series
      mainSeries = chart.addSeries(CandlestickSeries, {
        upColor: '#00ff88',
        downColor: '#ff3366',
        borderVisible: false,
        wickUpColor: '#00ff88',
        wickDownColor: '#ff3366',
        priceScaleId: 'right',
      });
      candleSeriesRef.current = mainSeries;
    }

    // Create volume series
    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: 'volume',
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ 
          width: chartContainerRef.current.clientWidth 
        });
      }
    };

    window.addEventListener('resize', handleResize);

    chartRef.current = chart;
    volumeSeriesRef.current = volumeSeries;

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [height, isLiveMode]);

  // Update data when priceData changes
  useEffect(() => {
    if (!priceData || !chartRef.current) return;

    setIsLoading(true);
    setError(null);

    try {
      if (isLiveMode && lineSeriesRef.current) {
        // Transform live data for line series
        const lineData = priceData.map(item => ({
          time: item.timestamp ? item.timestamp / 1000 : new Date(item.time).getTime() / 1000,
          value: item.price || item.close || 0,
        })).filter(item => item.value > 0);

        // Sort by time
        lineData.sort((a, b) => a.time - b.time);

        lineSeriesRef.current.setData(lineData);

        // Volume data
        if (volumeSeriesRef.current) {
          const volumeData = priceData.map(item => ({
            time: item.timestamp ? item.timestamp / 1000 : new Date(item.time).getTime() / 1000,
            value: item.volume || 0,
            color: 'rgba(38, 166, 154, 0.5)',
          }));
          volumeSeriesRef.current.setData(volumeData);
        }
      } else if (!isLiveMode && candleSeriesRef.current) {
        // Transform historical data for candlestick series
        const candleData = priceData.map(item => {
          const time = item.timestamp ? item.timestamp / 1000 : new Date(item.date || item.time).getTime() / 1000;
          return {
            time: time,
            open: item.open || item.price,
            high: item.high || item.price,
            low: item.low || item.price,
            close: item.close || item.price,
          };
        }).filter(item => item.close > 0);

        // Sort by time
        candleData.sort((a, b) => a.time - b.time);

        candleSeriesRef.current.setData(candleData);

        // Volume data
        if (volumeSeriesRef.current) {
          const volumeData = priceData.map(item => {
            const time = item.timestamp ? item.timestamp / 1000 : new Date(item.date || item.time).getTime() / 1000;
            return {
              time: time,
              value: item.volume || 0,
              color: (item.close || item.price) >= (item.open || item.price) 
                ? 'rgba(0, 255, 136, 0.5)' 
                : 'rgba(255, 51, 102, 0.5)',
            };
          });
          volumeSeriesRef.current.setData(volumeData);
        }
      }

      // Add trade markers
      if (userTrades.length > 0 && (candleSeriesRef.current || lineSeriesRef.current)) {
        const markers = userTrades.map(trade => ({
          time: trade.timestamp / 1000,
          position: trade.side === 'B' ? 'belowBar' : 'aboveBar',
          color: trade.side === 'B' ? '#00ff88' : '#ff3366',
          shape: trade.side === 'B' ? 'arrowUp' : 'arrowDown',
          text: `${trade.side === 'B' ? 'Buy' : 'Sell'} ${trade.size} @ $${trade.price}`,
        }));

        const series = candleSeriesRef.current || lineSeriesRef.current;
        series.setMarkers(markers);
        markersRef.current = markers;
      }

      // Fit content and scroll to recent data
      chartRef.current.timeScale().fitContent();
      
      // For live mode, scroll to the most recent data
      if (isLiveMode) {
        chartRef.current.timeScale().scrollToRealTime();
      }

      setIsLoading(false);
    } catch (err) {
      console.error('Error updating chart:', err);
      setError(err.message);
      setIsLoading(false);
    }
  }, [priceData, isLiveMode, userTrades]);

  return (
    <div className="price-chart-container">
      <div 
        ref={chartContainerRef} 
        className="chart-wrapper"
        style={{ position: 'relative', height: `${height}px` }}
      >
        {isLoading && (
          <div className="chart-loading">
            <div className="loading-spinner"></div>
            <p>Loading chart...</p>
          </div>
        )}
        {error && (
          <div className="chart-error">
            <p>Error: {error}</p>
          </div>
        )}
      </div>

      {!isLoading && !error && (
        <div className="chart-footer">
          <div className="chart-legend">
            <span className="legend-item">
              <span className="legend-color" style={{ backgroundColor: '#00ff88' }}></span>
              {isLiveMode ? 'Price' : 'Price Up'}
            </span>
            {!isLiveMode && (
              <span className="legend-item">
                <span className="legend-color" style={{ backgroundColor: '#ff3366' }}></span>
                Price Down
              </span>
            )}
            <span className="legend-item">
              <span className="legend-color" style={{ backgroundColor: '#26a69a' }}></span>
              Volume
            </span>
          </div>
          <div className="chart-controls">
            <button 
              className="chart-control-btn"
              onClick={() => chartRef.current?.timeScale().scrollToRealTime()}
              title="Go to latest"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M13 8l-5 5V9.5H2V6.5h6V3l5 5z"/>
              </svg>
            </button>
            <button 
              className="chart-control-btn"
              onClick={() => chartRef.current?.timeScale().fitContent()}
              title="Fit to screen"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M3.5 2.5a1 1 0 0 0-1 1v9a1 1 0 0 0 1 1h9a1 1 0 0 0 1-1v-9a1 1 0 0 0-1-1h-9zm-1-1h9a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-9a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2z"/>
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PriceChart; 