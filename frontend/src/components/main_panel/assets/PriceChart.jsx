import React, { useEffect, useRef, useState, useCallback } from 'react';
import { 
  createChart, 
  CrosshairMode, 
  LineStyle,
  LineSeries,
  CandlestickSeries,
  HistogramSeries
} from 'lightweight-charts';
import chartDataManager from '../../../services/ChartDataManager';
import './PriceChart.css';

const PriceChart = ({ 
  priceData: initialPriceData, 
  isLiveMode = false, 
  userTrades = [],
  symbol = 'BTC',
  quoteAsset = 'USD',
  height = 400,
  interval = '1h'
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
          const key = item.time || item.timestamp;
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
  }, [symbol, loadedData, interval]);

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
    let resizeObserver = null;
    let handleVisibleRangeChangeDebounced = null;

    const initializeChart = () => {
      if (!chartContainerRef.current || chartRef.current) return; // Already initialized or container gone

      const containerWidth = chartContainerRef.current.clientWidth;
      const containerHeight = height || chartContainerRef.current.clientHeight;

      console.log('Initializing chart with container:', chartContainerRef.current);
      console.log('Container dimensions for chart init:', {
        width: containerWidth,
        height: containerHeight,
        offsetHeight: chartContainerRef.current.offsetHeight,
        offsetWidth: chartContainerRef.current.offsetWidth,
      });

      if (containerWidth === 0 || containerHeight === 0) {
        console.warn('Chart container has zero dimensions. Will retry or wait for resize.');
        // If using ResizeObserver, it should pick up the change. Otherwise, consider a retry mechanism.
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
          secondsVisible: interval === '5m',
          tickMarkFormatter: (time, tickMarkType, locale) => {
            const date = new Date(time * 1000);
            
            if (interval === '5m') {
              // For 5m interval, show time with seconds
              return date.toLocaleTimeString(locale, { 
                hour: '2-digit', 
                minute: '2-digit',
                second: '2-digit'
              });
            } else if (interval === '1h') {
              // For 1h interval, show date and time
              return date.toLocaleDateString(locale, { 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              });
            } else {
              // For 1d interval, show just date
              return date.toLocaleDateString(locale, { 
                month: 'short', 
                day: 'numeric',
                year: 'numeric'
              });
            }
          },
          // Default barSpacing, let fitContent and zoom buttons handle it initially
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

      chartRef.current = chart;

      let mainSeries;
      if (isLiveMode) {
        mainSeries = chart.addSeries(LineSeries, {
          color: '#00ff88',
          lineWidth: 2,
          priceScaleId: 'right',
          lastValueVisible: true,
          priceLineVisible: true,
        });
        lineSeriesRef.current = mainSeries;
      } else {
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

      const volumeSeries = chart.addSeries(HistogramSeries, {
        color: '#26a69a',
        priceFormat: {
          type: 'volume',
        },
        priceScaleId: 'volume', // Ensure this is different from the main price scale ID if needed
        scaleMargins: {
          top: 0.98, // Greatly increased top margin to make volume bars much shorter (approx 1/10th of previous height)
          bottom: 0,
        },
      });
      volumeSeriesRef.current = volumeSeries;

      const debouncedLoadData = (from, to) => {
        if (handleVisibleRangeChangeDebounced) {
          clearTimeout(handleVisibleRangeChangeDebounced);
        }
        handleVisibleRangeChangeDebounced = setTimeout(() => {
          loadVisibleRangeData(from, to);
        }, 300); // Increased debounce time slightly
      };

      chart.timeScale().subscribeVisibleLogicalRangeChange(() => {
        if (!chartRef.current) return;
        const logicalRange = chartRef.current.timeScale().getVisibleLogicalRange();
        if (logicalRange) {
            // Convert logical range to timestamps for data loading
            // This conversion might be tricky if data isn't set yet, handle carefully.
            // For now, this seems to be based on existing data points coordinateToTime
            const timeScale = chartRef.current.timeScale();
            const firstBar = timeScale.coordinateToTime(0); // This might be null if no data
            const lastBar = timeScale.coordinateToTime(timeScale.width());

            if(firstBar && lastBar){
                setVisibleRange({ from: firstBar, to: lastBar }); // Store actual timestamps
                debouncedLoadData(firstBar, lastBar);
            } else {
                // Fallback or initial load if coordinateToTime is not yet reliable
                // This part might need refinement based on when data is available.
                console.warn("Visible range change triggered but coordinateToTime returned null, possibly no data yet for mapping coordinates.");
            }
        }
      });

      // Initial data load and zoom are handled in the other useEffect hook that depends on initialPriceData
      console.log("Chart initialized and series added.");
    };

    // Use ResizeObserver to handle container resize and initial setup
    if (chartContainerRef.current) {
      resizeObserver = new ResizeObserver(entries => {
        for (let entry of entries) {
          const { width, height } = entry.contentRect;
          if (width > 0 && height > 0) {
            if (!chartRef.current) {
              console.log('ResizeObserver: Container has dimensions, attempting to initialize chart.');
              initializeChart();
            } else {
              console.log('ResizeObserver: Resizing existing chart to', width, height);
              chartRef.current.resize(width, height);
            }
          }
        }
      });
      resizeObserver.observe(chartContainerRef.current);
    }
    
    // Attempt initial chart creation if dimensions are already good
    // This addresses cases where ResizeObserver might fire after initial render with dimensions
    if (chartContainerRef.current && chartContainerRef.current.clientWidth > 0 && chartContainerRef.current.clientHeight > 0 && !chartRef.current) {
        console.log("Attempting immediate chart initialization as container has dimensions.")
        initializeChart();
    }

    return () => {
      if (resizeObserver && chartContainerRef.current) {
        resizeObserver.unobserve(chartContainerRef.current);
      }
      if (handleVisibleRangeChangeDebounced) {
        clearTimeout(handleVisibleRangeChangeDebounced);
      }
      // Chart removal is now done in a separate effect to avoid premature removal
    };
  }, [height, isLiveMode, loadVisibleRangeData]); // Removed initialPriceData dependency here, handled separately
  
  // Effect for cleaning up the chart instance when the component unmounts or symbol changes
  useEffect(() => {
    return () => {
        if (chartRef.current) {
            console.log("Removing chart instance from DOM.");
            chartRef.current.remove();
            chartRef.current = null;
            // also clear series refs
            candleSeriesRef.current = null;
            lineSeriesRef.current = null;
            volumeSeriesRef.current = null;
        }
    }
  }, [symbol]); // Re-run this cleanup if symbol changes, implying a new chart should be made

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

    // Fit content after initial load with zoom out
    setTimeout(() => {
      if (chartRef.current) {
        const chart = chartRef.current;
        const timeScale = chart.timeScale();
        
        // First fit all content
        timeScale.fitContent();
        
        // Then set initial visible range based on interval configuration
        const initialRange = chartDataManager.getInitialVisibleRange(interval);
        const dataLength = initialPriceData.length;
        
        if (dataLength > initialRange.bars) {
          // Show only the last N bars as configured for the interval
          const newFrom = Math.max(0, dataLength - initialRange.bars);
          const newTo = dataLength - 1;
          
          timeScale.setVisibleLogicalRange({ from: newFrom, to: newTo });
        }
        
        // For 5m interval (live mode), scroll to the most recent data
        if (interval === '5m') {
          timeScale.scrollToRealTime();
        }
      }
    }, 100);
  }, [initialPriceData, interval, updateChartData]);

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
          height: `${height}px`
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
              onClick={() => {
                if (chartRef.current) {
                  const timeScale = chartRef.current.timeScale();
                  const logicalRange = timeScale.getVisibleLogicalRange();
                  if (logicalRange) {
                    const barCount = logicalRange.to - logicalRange.from;
                    const newBarCount = Math.floor(barCount * 0.7); // Zoom in by 30%
                    const center = (logicalRange.from + logicalRange.to) / 2;
                    const newFrom = center - newBarCount / 2;
                    const newTo = center + newBarCount / 2;
                    timeScale.setVisibleLogicalRange({ from: newFrom, to: newTo });
                  }
                }
              }}
              title="Zoom in"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M6.5 0a6.5 6.5 0 0 0-5.207 10.293l-1 1a1 1 0 0 0 0 1.414l1.586 1.586a1 1 0 0 0 1.414 0l1-1A6.5 6.5 0 1 0 6.5 0zm0 11a4.5 4.5 0 1 1 0-9 4.5 4.5 0 0 1 0 9z"/>
                <path d="M6.5 4a.5.5 0 0 1 .5.5V6h1.5a.5.5 0 0 1 0 1H7v1.5a.5.5 0 0 1-1 0V7H4.5a.5.5 0 0 1 0-1H6V4.5a.5.5 0 0 1 .5-.5z"/>
              </svg>
            </button>
            <button 
              className="chart-control-btn"
              onClick={() => {
                if (chartRef.current) {
                  const timeScale = chartRef.current.timeScale();
                  const logicalRange = timeScale.getVisibleLogicalRange();
                  if (logicalRange) {
                    const barCount = logicalRange.to - logicalRange.from;
                    const newBarCount = Math.floor(barCount * 1.4); // Zoom out by 40%
                    const center = (logicalRange.from + logicalRange.to) / 2;
                    const newFrom = Math.max(0, center - newBarCount / 2);
                    const newTo = center + newBarCount / 2;
                    timeScale.setVisibleLogicalRange({ from: newFrom, to: newTo });
                  }
                }
              }}
              title="Zoom out"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M6.5 0a6.5 6.5 0 0 0-5.207 10.293l-1 1a1 1 0 0 0 0 1.414l1.586 1.586a1 1 0 0 0 1.414 0l1-1A6.5 6.5 0 1 0 6.5 0zm0 11a4.5 4.5 0 1 1 0-9 4.5 4.5 0 0 1 0 9z"/>
                <path d="M4.5 6.5a.5.5 0 0 1 0-1h3a.5.5 0 0 1 0 1h-3z"/>
              </svg>
            </button>
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