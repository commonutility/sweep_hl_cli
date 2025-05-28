import React, { useState, useEffect } from 'react'
import './AssetPage.css'

const AssetPage = ({ symbol = 'BTC', timeRange = '6M' }) => {
  const [priceData, setPriceData] = useState(null)
  const [currentPrice, setCurrentPrice] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Map timeRange to days
  const timeRangeMap = {
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

  const fetchPriceData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Fetch current price
      const currentResponse = await fetch(`http://localhost:8000/api/assets/${symbol}/current`)
      if (!currentResponse.ok) throw new Error('Failed to fetch current price')
      const currentData = await currentResponse.json()
      setCurrentPrice(currentData)

      // Fetch historical data
      const days = timeRangeMap[timeRange] || 180
      const historyResponse = await fetch(`http://localhost:8000/api/assets/${symbol}/price-history?days=${days}`)
      if (!historyResponse.ok) throw new Error('Failed to fetch price history')
      const historyData = await historyResponse.json()
      setPriceData(historyData)
    } catch (err) {
      setError(err.message)
      console.error('Error fetching price data:', err)
    } finally {
      setLoading(false)
    }
  }

  const renderChart = () => {
    if (!priceData || priceData.length === 0) return null

    const width = 800
    const height = 500
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

    return (
      <svg width={width} height={height} className="price-chart">
        <defs>
          <linearGradient id="priceGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#4a7c59" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#4a7c59" stopOpacity="0" />
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
                stroke="#333"
                strokeDasharray="2,2"
              />
            ))}

            {/* Area fill */}
            <path d={areaPath} fill="url(#priceGradient)" />

            {/* Price line */}
            <path d={pricePath} fill="none" stroke="#4a7c59" strokeWidth="2" />

            {/* Y-axis labels */}
            {priceLabels.map((label, i) => (
              <text
                key={i}
                x={-10}
                y={label.y + 5}
                textAnchor="end"
                fill="#999"
                fontSize="12"
              >
                ${label.price.toFixed(2)}
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
                  fill={isGreen ? '#4a7c59' : '#c53030'}
                  opacity="0.6"
                />
              )
            })}

            {/* Volume axis line */}
            <line
              x1={0}
              y1={volumeHeight}
              x2={chartWidth}
              y2={volumeHeight}
              stroke="#333"
            />

            {/* Volume label */}
            <text
              x={-10}
              y={volumeHeight / 2}
              textAnchor="end"
              fill="#999"
              fontSize="10"
              transform={`rotate(-90, -10, ${volumeHeight / 2})`}
            >
              Volume
            </text>
          </g>

          {/* X-axis labels */}
          <g transform={`translate(0, ${chartHeight})`}>
            {[0, Math.floor(priceData.length / 2), priceData.length - 1].map(i => {
              const date = new Date(priceData[i].timestamp)
              return (
                <text
                  key={i}
                  x={xScale(i)}
                  y={20}
                  textAnchor="middle"
                  fill="#999"
                  fontSize="12"
                >
                  {date.toLocaleDateString()}
                </text>
              )
            })}
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

  const priceChange = currentPrice ? 
    ((currentPrice.price - currentPrice.price_24h_ago) / currentPrice.price_24h_ago * 100).toFixed(2) : 
    0

  return (
    <div className="asset-page">
      <div className="asset-header">
        <h1>{symbol}/USD</h1>
        <div className="price-info">
          <span className="current-price">${currentPrice?.price.toFixed(2)}</span>
          <span className={`price-change ${priceChange >= 0 ? 'positive' : 'negative'}`}>
            {priceChange >= 0 ? '+' : ''}{priceChange}%
          </span>
        </div>
      </div>

      <div className="time-range-selector">
        {Object.keys(timeRangeMap).map(range => (
          <button
            key={range}
            className={`time-range-btn ${timeRange === range ? 'active' : ''}`}
            onClick={() => {
              // This would normally trigger a re-render with new props
              // For now, we'll just log it
              console.log(`Time range changed to: ${range}`)
            }}
          >
            {range}
          </button>
        ))}
      </div>

      <div className="chart-container">
        {renderChart()}
      </div>

      <div className="asset-stats">
        <div className="stat">
          <span className="stat-label">24h High</span>
          <span className="stat-value">${currentPrice?.high_24h?.toFixed(2) || 'N/A'}</span>
        </div>
        <div className="stat">
          <span className="stat-label">24h Low</span>
          <span className="stat-value">${currentPrice?.low_24h?.toFixed(2) || 'N/A'}</span>
        </div>
        <div className="stat">
          <span className="stat-label">24h Volume</span>
          <span className="stat-value">${currentPrice?.volume_24h?.toLocaleString() || 'N/A'}</span>
        </div>
      </div>
    </div>
  )
}

export default AssetPage 