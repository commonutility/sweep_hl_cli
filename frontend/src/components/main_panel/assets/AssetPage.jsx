import React, { useState, useEffect } from 'react'
import OrderBook from './OrderBook'
import './AssetPage.css'

const AssetPage = ({ symbol = 'BTC', timeRange: initialTimeRange = '6M' }) => {
  const [priceData, setPriceData] = useState(null)
  const [currentPrice, setCurrentPrice] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [priceFlash, setPriceFlash] = useState(false)
  const [timeRange, setTimeRange] = useState(initialTimeRange)
  const [isLiveMode, setIsLiveMode] = useState(false)

  // Map timeRange to days
  const timeRangeMap = {
    'Live': 0,  // Special case for live data
    '1D': 1,
    '1W': 7,
    '1M': 30,
    '3M': 90,
    '6M': 180,
    '1Y': 365
  }

  useEffect(() => {
    fetchPriceData()
  }, [symbol, timeRange])

  useEffect(() => {
    // Set up periodic refresh
    let interval;
    
    if (timeRange === 'Live') {
      // Refresh every 10 seconds for live data
      interval = setInterval(() => {
        fetchPriceData()
      }, 10000)
    } else {
      // Refresh current price every 5 seconds for other views
      interval = setInterval(() => {
        fetchCurrentPrice()
      }, 5000)
    }

    return () => clearInterval(interval)
  }, [symbol, timeRange])

  const fetchCurrentPrice = async () => {
    try {
      console.log(`[AssetPage] Fetching current price for ${symbol}...`)
      const response = await fetch(`http://localhost:8000/api/assets/${symbol}/current`)
      if (!response.ok) throw new Error('Failed to fetch current price')
      const data = await response.json()
      
      console.log(`[AssetPage] Received price data:`, data)
      
      // Check if price changed
      if (currentPrice && data.price !== currentPrice.price) {
        console.log(`[AssetPage] Price changed from ${currentPrice.price} to ${data.price}`)
        setPriceFlash(true)
        setTimeout(() => setPriceFlash(false), 500)
      }
      
      setCurrentPrice(data)
      setLastUpdate(new Date())
      console.log(`[AssetPage] Updated ${symbol} price:`, data.price, 'at', new Date().toLocaleTimeString())
    } catch (err) {
      console.error('Error fetching current price:', err)
    }
  }

  const fetchPriceData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Fetch current price
      await fetchCurrentPrice()

      if (timeRange === 'Live') {
        // Fetch live minute-level data
        setIsLiveMode(true)
        const liveResponse = await fetch(`http://localhost:8000/api/assets/${symbol}/live-data?minutes=30`)
        if (!liveResponse.ok) throw new Error('Failed to fetch live data')
        const liveData = await liveResponse.json()
        
        if (liveData && liveData.data && Array.isArray(liveData.data)) {
          setPriceData(liveData.data)
        } else {
          console.error('Invalid live data format:', liveData)
          setError('Invalid data format received from server')
        }
      } else {
        // Fetch historical data
        setIsLiveMode(false)
        const days = timeRangeMap[timeRange] || 180
        const historyResponse = await fetch(`http://localhost:8000/api/assets/${symbol}/price-history?days=${days}`)
        if (!historyResponse.ok) throw new Error('Failed to fetch price history')
        const historyData = await historyResponse.json()
        
        if (historyData && historyData.data && Array.isArray(historyData.data)) {
          setPriceData(historyData.data)
        } else {
          console.error('Invalid price data format:', historyData)
          setError('Invalid data format received from server')
        }
      }
    } catch (err) {
      setError(err.message)
      console.error('Error fetching price data:', err)
    } finally {
      setLoading(false)
    }
  }

  const renderChart = () => {
    if (!priceData || !Array.isArray(priceData) || priceData.length === 0) {
      return <div className="no-data">No price data available</div>
    }

    const width = 600
    const height = 400
    const padding = { top: 20, right: 60, bottom: 40, left: 60 }
    const chartWidth = width - padding.left - padding.right
    const chartHeight = height - padding.top - padding.bottom
    
    // Split chart area: 70% for price, 30% for volume
    const priceHeight = chartHeight * 0.7
    const volumeHeight = chartHeight * 0.25
    const gap = chartHeight * 0.05

    // Calculate price range
    const prices = priceData.map(d => d.close)
    const minPrice = Math.min(...prices) * 0.99
    const maxPrice = Math.max(...prices) * 1.01
    const priceRange = maxPrice - minPrice

    // Calculate volume range
    const volumes = priceData.map(d => d.volume || 0)
    const maxVolume = Math.max(...volumes) * 1.1

    // Create scales
    const xScale = (index) => (index / (priceData.length - 1)) * chartWidth
    const priceYScale = (price) => priceHeight - ((price - minPrice) / priceRange) * priceHeight
    const volumeYScale = (volume) => volumeHeight - (volume / maxVolume) * volumeHeight

    // Create price line path
    const pricePath = priceData
      .map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${priceYScale(d.close)}`)
      .join(' ')

    // Create area path for gradient
    const areaPath = pricePath + 
      ` L ${xScale(priceData.length - 1)} ${priceHeight} L ${xScale(0)} ${priceHeight} Z`

    // Y-axis labels for price
    const priceLabels = []
    const labelCount = 5
    for (let i = 0; i <= labelCount; i++) {
      const price = minPrice + (priceRange * i / labelCount)
      const y = priceYScale(price)
      priceLabels.push({ price, y })
    }

    // Format x-axis labels based on whether it's live data or historical
    const getXAxisLabels = () => {
      if (isLiveMode) {
        // For live data, show time labels
        const labelIndices = [0, Math.floor(priceData.length / 2), priceData.length - 1]
        return labelIndices.map(i => ({
          index: i,
          label: priceData[i].time || new Date(priceData[i].timestamp).toLocaleTimeString()
        }))
      } else {
        // For historical data, show date labels
        const labelIndices = [0, Math.floor(priceData.length / 2), priceData.length - 1]
        return labelIndices.map(i => ({
          index: i,
          label: new Date(priceData[i].timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
        }))
      }
    }

    const xAxisLabels = getXAxisLabels()

    return (
      <svg width={width} height={height} className="price-chart">
        <defs>
          <linearGradient id="priceGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#ffffff" stopOpacity="0.1" />
            <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
          </linearGradient>
        </defs>

        <g transform={`translate(${padding.left}, ${padding.top})`}>
          {/* Price Chart */}
          <g>
            {/* Grid lines */}
            {priceLabels.map((label, i) => (
              <line
                key={i}
                x1={0}
                y1={label.y}
                x2={chartWidth}
                y2={label.y}
                stroke="#2a2a2a"
                strokeDasharray="2,2"
                opacity="0.5"
              />
            ))}

            {/* Area fill */}
            <path d={areaPath} fill="url(#priceGradient)" />

            {/* Price line */}
            <path d={pricePath} fill="none" stroke="#ffffff" strokeWidth="2" />

            {/* Y-axis labels */}
            {priceLabels.map((label, i) => (
              <text
                key={i}
                x={-10}
                y={label.y + 5}
                textAnchor="end"
                fill="#666"
                fontSize="11"
              >
                ${label.price.toFixed(0)}
              </text>
            ))}
          </g>

          {/* Volume Chart */}
          <g transform={`translate(0, ${priceHeight + gap})`}>
            {/* Volume bars */}
            {priceData.map((d, i) => {
              const barWidth = chartWidth / priceData.length * 0.8
              const barX = xScale(i) - barWidth / 2
              const barHeight = (d.volume / maxVolume) * volumeHeight
              const barY = volumeHeight - barHeight
              const isGreen = d.close >= d.open
              
              return (
                <rect
                  key={i}
                  x={barX}
                  y={barY}
                  width={barWidth}
                  height={barHeight}
                  fill={isGreen ? '#00ff88' : '#ff3366'}
                  opacity="0.4"
                />
              )
            })}

            {/* Volume axis line */}
            <line
              x1={0}
              y1={volumeHeight}
              x2={chartWidth}
              y2={volumeHeight}
              stroke="#2a2a2a"
              opacity="0.5"
            />

            {/* Volume label */}
            <text
              x={-10}
              y={volumeHeight / 2}
              textAnchor="end"
              fill="#666"
              fontSize="10"
              transform={`rotate(-90, -10, ${volumeHeight / 2})`}
            >
              Volume
            </text>
          </g>

          {/* X-axis labels */}
          <g transform={`translate(0, ${chartHeight})`}>
            {xAxisLabels.map(({ index, label }) => (
              <text
                key={index}
                x={xScale(index)}
                y={20}
                textAnchor="middle"
                fill="#666"
                fontSize="11"
              >
                {label}
              </text>
            ))}
          </g>
        </g>
      </svg>
    )
  }

  if (loading) {
    return (
      <div className="asset-page">
        <div className="loading">Loading {symbol} data...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="asset-page">
        <div className="error">Error: {error}</div>
      </div>
    )
  }

  const priceChange = currentPrice && currentPrice.price_24h_ago ? 
    ((currentPrice.price - currentPrice.price_24h_ago) / currentPrice.price_24h_ago * 100).toFixed(2) : 
    null

  const priceChangePercent = currentPrice?.price_change_percent?.toFixed(2) || priceChange || '0.00'

  return (
    <div className="asset-page">
      <div className="asset-header">
        <h1>{symbol}/USD</h1>
        <div className="price-info">
          <span className={`current-price ${priceFlash ? 'price-flash' : ''}`}>
            ${currentPrice?.price?.toFixed(2) || '---'}
          </span>
          <span className={`price-change ${parseFloat(priceChangePercent) >= 0 ? 'positive' : 'negative'}`}>
            {parseFloat(priceChangePercent) >= 0 ? '+' : ''}{priceChangePercent}%
          </span>
          {lastUpdate && (
            <span className="last-update">
              Updated: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <button 
            onClick={fetchCurrentPrice} 
            className="refresh-button"
            title="Refresh price"
          >
            🔄
          </button>
        </div>
        {currentPrice?.bid && currentPrice?.ask && (
          <div className="bid-ask-info">
            <span className="bid">Bid: ${currentPrice.bid.toFixed(2)}</span>
            <span className="spread">Spread: ${currentPrice.spread?.toFixed(2)} ({currentPrice.spread_percentage?.toFixed(3)}%)</span>
            <span className="ask">Ask: ${currentPrice.ask.toFixed(2)}</span>
          </div>
        )}
      </div>

      <div className="time-range-selector">
        {Object.keys(timeRangeMap).map(range => (
          <button
            key={range}
            className={`time-range-btn ${timeRange === range ? 'active' : ''}`}
            onClick={() => {
              setTimeRange(range)
              console.log(`Time range changed to: ${range}`)
            }}
          >
            {range}
          </button>
        ))}
      </div>

      <div className="chart-and-orderbook-container">
        <div className="chart-container">
          {renderChart()}
        </div>
        <div className="orderbook-container">
          <OrderBook symbol={symbol} />
        </div>
      </div>

      <div className="asset-stats">
        <div className="stat">
          <span className="stat-label">24h High</span>
          <span className="stat-value">${currentPrice?.high_24h?.toFixed(2) || '---'}</span>
        </div>
        <div className="stat">
          <span className="stat-label">24h Low</span>
          <span className="stat-value">${currentPrice?.low_24h?.toFixed(2) || '---'}</span>
        </div>
        <div className="stat">
          <span className="stat-label">24h Volume</span>
          <span className="stat-value">
            {currentPrice?.volume_24h ? 
              formatVolume(currentPrice.volume_24h) : 
              '---'
            }
          </span>
        </div>
        <div className="stat">
          <span className="stat-label">24h Change</span>
          <span className={`stat-value ${currentPrice?.price_change >= 0 ? 'positive' : 'negative'}`}>
            ${Math.abs(currentPrice?.price_change || 0).toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  )
}

// Helper function to format volume
const formatVolume = (volume) => {
  if (volume >= 1000000) {
    return `$${(volume / 1000000).toFixed(2)}M`
  } else if (volume >= 1000) {
    return `$${(volume / 1000).toFixed(2)}K`
  } else {
    return `$${volume.toFixed(2)}`
  }
}

export default AssetPage 