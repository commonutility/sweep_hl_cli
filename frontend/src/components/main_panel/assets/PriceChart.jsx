import React, { useEffect, useRef, useState, useCallback } from 'react';
import { createChart, CrosshairMode, LineStyle } from 'lightweight-charts';
import chartDataManager from '../../../services/ChartDataManager';
import './PriceChart.css';

const PriceChart = ({ 
  priceData: initialPriceData, 
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
  const [loadedData, setLoadedData] = useState(new Map());
  const [visibleRange, setVisibleRange] = useState(null);
  const isLoadingRef = useRef(false);
  const lastLoadedRangeRef = useRef(null);

  // Get interval based on visible range
  const getIntervalForRange = useCallback((from, to) => {
    const rangeInDays = (to - from) / (24 * 3600);
    
    if (rangeInDays <= 1) return '1m';
    if (rangeInDays <= 7) return '5m';
    if (rangeInDays <= 30) return '15m';
    if (rangeInDays <= 90) return '1h';
    if (rangeInDays <= 365) return '4h';
    return '1d';
  }, []);

  // Load data for visible range
  const loadVisibleRangeData = useCallback(async (from, to) => {
    if (!symbol || isLoadingRef.current) return;

    // Check if we've already loaded this range
    if (lastLoadedRangeRef.current) {
      const { from: lastFrom, to: lastTo } = lastLoadedRangeRef.current;
      if (from >= lastFrom && to <= lastTo) {
        return; // Data already loaded
      }
    }

    isLoadingRef.current = true;
    setIsLoading(true);

    try {
      const interval = getIntervalForRange(from, to);
      
      // Add buffer to load more data than visible
      const bufferRatio = 0.5;
      const range = to - from;
      const bufferSize = range * bufferRatio;
      const bufferedFrom = from - bufferSize;
      const bufferedTo = to + bufferSize;

      // Convert to milliseconds for the data manager
      const fromMs = bufferedFrom * 1000;
      const toMs = bufferedTo * 1000;

      const data = await chartDataManager.loadDataRange(
        symbol,
        fromMs,
        toMs,
        interval
      );

      if (data && data.length > 0) {
        // Update loaded data
        const newLoadedData = new Map(loadedData);
        data.forEach(item => {
          const key = item.timestamp || new Date(item.date || item.time).getTime();
          newLoadedData.set(key, item);
        });
        setLoadedData(newLoadedData);

        // Update chart
        updateChartData(Array.from(newLoadedData.values()));

        // Update last loaded range
        lastLoadedRangeRef.current = { from: bufferedFrom, to: bufferedTo };

        // Prefetch adjacent data
        chartDataManager.prefetchAdjacent(symbol, fromMs, toMs, interval);
      }
    } catch (err) {
      console.error('Error loading chart data:', err);
      setError(err.message);
    } finally {
      isLoadingRef.current = false;
      setIsLoading(false);
    }
  }, [symbol, loadedData, getIntervalForRange]);

  // Update chart with new data
  const updateChartData = useCallback((data) => {
    if (!data || data.length === 0) {
      console.warn('No data to update chart with');
      return;
    }

    console.log('Updating chart with data:', {
      dataLength: data.length,
      firstItem: data[0],
      lastItem: data[data.length - 1],
      isLiveMode,
      hasLineSeries: !!lineSeriesRef.current,
      hasCandleSeries: !!candleSeriesRef.current
    });

    try {
      if (isLiveMode && lineSeriesRef.current) {
        // Transform for line series
        const lineData = data.map(item => ({
          time: item.timestamp ? item.timestamp / 1000 : new Date(item.time).getTime() / 1000,
          value: item.price || item.close || 0,
        })).filter(item => item.value > 0);

        lineData.sort((a, b) => a.time - b.time);
        
        console.log('Setting line data:', {
          dataLength: lineData.length,
          firstPoint: lineData[0],
          lastPoint: lineData[lineData.length - 1]
        });
        
        lineSeriesRef.current.setData(lineData);

        // Volume data
        if (volumeSeriesRef.current) {
          const volumeData = data.map(item => ({
            time: item.timestamp ? item.timestamp / 1000 : new Date(item.time).getTime() / 1000,
            value: item.volume || 0,
            color: 'rgba(38, 166, 154, 0.5)',
          }));
          volumeSeriesRef.current.setData(volumeData);
        }
      } else if (!isLiveMode && candleSeriesRef.current) {
        // Transform for candlestick series
        const candleData = data.map(item => {
          const time = item.timestamp ? item.timestamp / 1000 : new Date(item.date || item.time).getTime() / 1000;
          return {
            time: time,
            open: item.open || item.price,
            high: item.high || item.price,
            low: item.low || item.price,
            close: item.close || item.price,
          };
        }).filter(item => item.close > 0);

        candleData.sort((a, b) => a.time - b.time);
        candleSeriesRef.current.setData(candleData);

        // Volume data
        if (volumeSeriesRef.current) {
          const volumeData = data.map(item => {
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
    } catch (err) {
      console.error('Error updating chart:', err);
    }
  }, [isLiveMode, userTrades]);

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    let chart = null;
    let handleResize = null;
    let handleVisibleRangeChange = null;

    // Small delay to ensure container is properly rendered
    const initTimer = setTimeout(() => {
      if (!chartContainerRef.current) return;

      const containerWidth = chartContainerRef.current.clientWidth;
      const containerHeight = height || chartContainerRef.current.clientHeight;

      console.log('Initializing chart with container:', chartContainerRef.current);
      console.log('Container dimensions:', {
        width: containerWidth,
        height: containerHeight,
        offsetWidth: chartContainerRef.current.offsetWidth,
        offsetHeight: chartContainerRef.current.offsetHeight
      });

      // Don't create chart if container has no dimensions
      if (containerWidth === 0 || containerHeight === 0) {
        console.error('Container has no dimensions, retrying...');
        setTimeout(() => {
          if (chartContainerRef.current) {
            const retryWidth = chartContainerRef.current.clientWidth;
            const retryHeight = height || chartContainerRef.current.clientHeight;
            if (retryWidth > 0 && retryHeight > 0) {
              // Trigger re-render by updating a state
              setError(null);
            }
          }
        }, 100);
        return;
      }

      chart = createChart(chartContainerRef.current, {
        width: containerWidth,
        height: containerHeight,
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
              return date.toLocaleTimeString(locale, { 
                hour: '2-digit', 
                minute: '2-digit',
                second: '2-digit'
              });
            } else {
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
        mainSeries = chart.addLineSeries({
          color: '#00ff88',
          lineWidth: 2,
          priceScaleId: 'right',
          lastValueVisible: true,
          priceLineVisible: true,
        });
        lineSeriesRef.current = mainSeries;
      } else {
        mainSeries = chart.addCandlestickSeries({
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
      const volumeSeries = chart.addHistogramSeries({
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

      // Handle visible range changes
      handleVisibleRangeChange = () => {
        const timeScale = chart.timeScale();
        const range = timeScale.getVisibleLogicalRange();
        
        if (range) {
          setVisibleRange(range);
          
          // Debounced data loading
          if (handleVisibleRangeChange.timer) {
            clearTimeout(handleVisibleRangeChange.timer);
          }
          
          handleVisibleRangeChange.timer = setTimeout(() => {
            // Convert logical range to timestamps
            const visibleData = chartRef.current?.timeScale().coordinateToTime(0);
            const visibleDataEnd = chartRef.current?.timeScale().coordinateToTime(chartRef.current.timeScale().width());
            
            if (visibleData && visibleDataEnd) {
              loadVisibleRangeData(visibleData, visibleDataEnd);
            }
          }, 200);
        }
      };

      // Subscribe to visible range changes
      chart.timeScale().subscribeVisibleLogicalRangeChange(handleVisibleRangeChange);

      // Handle resize
      handleResize = () => {
        if (chartContainerRef.current && chart) {
          chart.applyOptions({ 
            width: chartContainerRef.current.clientWidth 
          });
        }
      };

      window.addEventListener('resize', handleResize);

      chartRef.current = chart;
      volumeSeriesRef.current = volumeSeries;
    }, 50); // 50ms delay

    return () => {
      clearTimeout(initTimer);
      if (handleResize) {
        window.removeEventListener('resize', handleResize);
      }
      if (chart && handleVisibleRangeChange) {
        chart.timeScale().unsubscribeVisibleLogicalRangeChange(handleVisibleRangeChange);
        chart.remove();
      }
    };
  }, [height, isLiveMode, loadVisibleRangeData]);

  // Load initial data
  useEffect(() => {
    if (!chartRef.current || !initialPriceData) {
      console.log('Skipping initial data load:', {
        hasChart: !!chartRef.current,
        hasData: !!initialPriceData,
        dataLength: initialPriceData?.length
      });
      return;
    }

    console.log('Loading initial data:', {
      chartRef: chartRef.current,
      dataLength: initialPriceData?.length,
      symbol,
      isLiveMode
    });

    // Clear existing data
    setLoadedData(new Map());
    lastLoadedRangeRef.current = null;

    // Convert initial data to map
    const dataMap = new Map();
    initialPriceData.forEach(item => {
      const key = item.timestamp || new Date(item.date || item.time).getTime();
      dataMap.set(key, item);
    });
    setLoadedData(dataMap);

    // Update chart
    updateChartData(initialPriceData);

    // Fit content after initial load
    setTimeout(() => {
      if (chartRef.current) {
        chartRef.current.timeScale().fitContent();
        
        // For live mode, scroll to the most recent data
        if (isLiveMode) {
          chartRef.current.timeScale().scrollToRealTime();
        }
      }
    }, 100);
  }, [initialPriceData, isLiveMode, updateChartData]);

  // Clear cache when symbol changes
  useEffect(() => {
    return () => {
      if (symbol) {
        chartDataManager.clearSymbolCache(symbol);
      }
    };
  }, [symbol]);

  return (
    <div className="price-chart-container">
      <div 
        ref={chartContainerRef} 
        className="chart-wrapper"
        style={{ 
          position: 'relative', 
          height: `${height}px`,
          backgroundColor: '#1a1a1a' // Temporary background to ensure visibility
        }}
      >
        {isLoading && loadedData.size === 0 && (
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
        {!isLoading && !error && loadedData.size === 0 && !initialPriceData && (
          <div className="chart-loading">
            <p>No data available</p>
          </div>
        )}
      </div>

      {loadedData.size > 0 && (
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
            {isLoading && loadedData.size > 0 && (
              <span className="loading-indicator">Loading...</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PriceChart; 