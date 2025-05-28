import React, { memo } from 'react'

const PriceChart = memo(({ priceData, isLiveMode, userTrades = [] }) => {
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

  // Get time range for x-axis scaling
  const timeRange = {
    min: Math.min(...priceData.map(d => d.timestamp)),
    max: Math.max(...priceData.map(d => d.timestamp))
  }
  const timeDiff = timeRange.max - timeRange.min

  // Create scales
  const xScale = (index) => (index / (priceData.length - 1)) * chartWidth
  const xScaleTime = (timestamp) => ((timestamp - timeRange.min) / timeDiff) * chartWidth
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

          {/* User trades as dots */}
          {userTrades.map((trade, i) => {
            // Only show trades within the time range
            if (trade.timestamp < timeRange.min || trade.timestamp > timeRange.max) {
              return null
            }
            
            const x = xScaleTime(trade.timestamp)
            const y = priceYScale(trade.price)
            const isBuy = trade.side === 'B'
            
            return (
              <g key={`trade-${i}`}>
                <circle
                  cx={x}
                  cy={y}
                  r="6"
                  fill={isBuy ? '#00ff88' : '#ff3366'}
                  stroke="#ffffff"
                  strokeWidth="2"
                  opacity="0.9"
                  className="trade-dot"
                />
                {/* Tooltip on hover */}
                <title>
                  {isBuy ? 'Buy' : 'Sell'} {trade.size} @ ${trade.price.toFixed(2)}
                  {'\n'}{new Date(trade.timestamp).toLocaleString()}
                </title>
              </g>
            )
          })}

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
}, (prevProps, nextProps) => {
  // Custom comparison function for memo
  // Only re-render if data actually changed
  return (
    prevProps.isLiveMode === nextProps.isLiveMode &&
    prevProps.priceData?.length === nextProps.priceData?.length &&
    prevProps.priceData?.[0]?.timestamp === nextProps.priceData?.[0]?.timestamp &&
    prevProps.priceData?.[prevProps.priceData.length - 1]?.timestamp === 
      nextProps.priceData?.[nextProps.priceData.length - 1]?.timestamp &&
    prevProps.userTrades?.length === nextProps.userTrades?.length
  )
})

PriceChart.displayName = 'PriceChart'

export default PriceChart 