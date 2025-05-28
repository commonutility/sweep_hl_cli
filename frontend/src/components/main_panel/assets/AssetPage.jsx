import { useState, useEffect } from 'react'
import './AssetPage.css'
import { getPriceHistory } from '../../../services/api'

const AssetPage = ({ symbol = 'BTC' }) => {
  const [priceData, setPriceData] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchPriceData = async () => {
      try {
        setIsLoading(true)
        setError(null)
        
        const response = await getPriceHistory(symbol, 180)
        setPriceData(response.data)
      } catch (err) {
        console.error('Error fetching price data:', err)
        setError(err.message)
      } finally {
        setIsLoading(false)
      }
    }

    fetchPriceData()
  }, [symbol])

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(price)
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  const formatVolume = (volume, price) => {
    // Volume is in asset terms (e.g., BTC), convert to USD
    const usdVolume = volume * price
    if (usdVolume >= 1000000000) {
      return `$${(usdVolume / 1000000000).toFixed(2)}B`
    } else if (usdVolume >= 1000000) {
      return `$${(usdVolume / 1000000).toFixed(2)}M`
    } else if (usdVolume >= 1000) {
      return `$${(usdVolume / 1000).toFixed(2)}K`
    }
    return `$${usdVolume.toFixed(2)}`
  }

  const formatYAxisPrice = (price) => {
    if (price >= 1000) {
      return `$${(price / 1000).toFixed(0)}k`
    }
    return `$${price.toFixed(0)}`
  }

  if (isLoading) {
    return (
      <div className="asset-page">
        <div className="loading-state">Loading price data...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="asset-page">
        <div className="error-state">Error loading price data: {error}</div>
      </div>
    )
  }

  const currentPrice = priceData[priceData.length - 1]?.price || 0
  const firstPrice = priceData[0]?.price || 0
  const priceChange = currentPrice - firstPrice
  const priceChangePercent = (priceChange / firstPrice) * 100

  // Calculate high and low from the data
  const highPrice = Math.max(...priceData.map(d => d.high))
  const lowPrice = Math.min(...priceData.map(d => d.low))
  
  // Calculate average daily volume in USD
  const avgVolumeUSD = priceData.reduce((sum, d) => sum + (d.volume * d.price), 0) / priceData.length

  // Calculate min and max prices for chart scaling
  const minPrice = Math.min(...priceData.map(d => d.low))
  const maxPrice = Math.max(...priceData.map(d => d.high))
  const priceRange = maxPrice - minPrice
  const padding = priceRange * 0.1 // Add 10% padding
  const chartMin = minPrice - padding
  const chartMax = maxPrice + padding

  // Calculate max volume for scaling
  const maxVolume = Math.max(...priceData.map(d => d.volume * d.price))

  // Generate y-axis labels for price
  const yAxisSteps = 5
  const yAxisLabels = []
  for (let i = 0; i <= yAxisSteps; i++) {
    const price = chartMin + (chartMax - chartMin) * (i / yAxisSteps)
    yAxisLabels.push({
      price,
      y: 250 - (i / yAxisSteps) * 200
    })
  }

  // Generate y-axis labels for volume
  const volumeAxisLabels = []
  for (let i = 0; i <= 2; i++) {
    const volume = (maxVolume * i) / 2
    volumeAxisLabels.push({
      volume,
      y: 450 - (i / 2) * 100
    })
  }

  return (
    <div className="asset-page">
      <div className="asset-header">
        <h1 className="asset-symbol">{symbol}</h1>
        <div className="price-info">
          <div className="current-price">{formatPrice(currentPrice)}</div>
          <div className={`price-change ${priceChange >= 0 ? 'positive' : 'negative'}`}>
            {priceChange >= 0 ? '+' : ''}{formatPrice(priceChange)} ({priceChangePercent.toFixed(2)}%)
          </div>
        </div>
      </div>

      <div className="chart-container">
        <div className="chart-header">
          <h2>6 Month Price & Volume History</h2>
        </div>
        <div className="price-chart">
          {/* Combined price and volume chart */}
          <svg viewBox="0 0 800 500" className="chart-svg">
            {/* Price Chart Section */}
            {/* Y-axis line for price */}
            <line
              x1="50"
              y1="50"
              x2="50"
              y2="250"
              stroke="#666"
              strokeWidth="1"
            />
            
            {/* Y-axis labels for price */}
            {yAxisLabels.map((label, i) => (
              <g key={`y-${i}`}>
                <text
                  x="45"
                  y={label.y + 5}
                  textAnchor="end"
                  fill="#999"
                  fontSize="11"
                >
                  {formatYAxisPrice(label.price)}
                </text>
                <line
                  x1="50"
                  y1={label.y}
                  x2="750"
                  y2={label.y}
                  stroke="#333"
                  strokeDasharray="2,2"
                />
              </g>
            ))}
            
            {/* Price line */}
            <polyline
              fill="none"
              stroke="#4ade80"
              strokeWidth="2"
              points={priceData.map((d, i) => {
                const x = 50 + (i / (priceData.length - 1)) * 700
                const y = 250 - ((d.price - chartMin) / (chartMax - chartMin)) * 200
                return `${x},${y}`
              }).join(' ')}
            />
            
            {/* Divider between price and volume */}
            <line
              x1="50"
              y1="250"
              x2="750"
              y2="250"
              stroke="#666"
              strokeWidth="1"
            />
            
            {/* Volume Chart Section */}
            {/* Y-axis line for volume */}
            <line
              x1="50"
              y1="250"
              x2="50"
              y2="450"
              stroke="#666"
              strokeWidth="1"
            />
            
            {/* Y-axis labels for volume */}
            {volumeAxisLabels.map((label, i) => (
              <g key={`vol-y-${i}`}>
                <text
                  x="45"
                  y={label.y + 5}
                  textAnchor="end"
                  fill="#999"
                  fontSize="10"
                >
                  {formatVolume(label.volume, 1).replace('$', '')}
                </text>
                {i > 0 && (
                  <line
                    x1="50"
                    y1={label.y}
                    x2="750"
                    y2={label.y}
                    stroke="#333"
                    strokeDasharray="2,2"
                  />
                )}
              </g>
            ))}
            
            {/* Volume bars */}
            {priceData.map((d, i) => {
              const x = 50 + (i / (priceData.length - 1)) * 700
              const barWidth = Math.max(1, 700 / priceData.length - 1)
              const volumeHeight = ((d.volume * d.price) / maxVolume) * 100
              const isGreen = d.close >= d.open
              
              return (
                <rect
                  key={`vol-${i}`}
                  x={x - barWidth / 2}
                  y={450 - volumeHeight}
                  width={barWidth}
                  height={volumeHeight}
                  fill={isGreen ? '#4ade80' : '#ef4444'}
                  opacity="0.6"
                />
              )
            })}
            
            {/* X-axis line */}
            <line
              x1="50"
              y1="450"
              x2="750"
              y2="450"
              stroke="#666"
              strokeWidth="1"
            />
            
            {/* X-axis labels */}
            {[0, 30, 60, 90, 120, 150, 179].map(dayIndex => {
              if (priceData[dayIndex]) {
                const x = 50 + (dayIndex / 179) * 700
                return (
                  <text
                    key={`x-${dayIndex}`}
                    x={x}
                    y={480}
                    textAnchor="middle"
                    fill="#999"
                    fontSize="12"
                  >
                    {formatDate(priceData[dayIndex].date)}
                  </text>
                )
              }
              return null
            })}
            
            {/* Labels for sections */}
            <text
              x="25"
              y="150"
              textAnchor="middle"
              fill="#999"
              fontSize="10"
              transform="rotate(-90 25 150)"
            >
              Price
            </text>
            <text
              x="25"
              y="350"
              textAnchor="middle"
              fill="#999"
              fontSize="10"
              transform="rotate(-90 25 350)"
            >
              Volume
            </text>
          </svg>
        </div>
      </div>

      <div className="price-stats">
        <div className="stat-item">
          <span className="stat-label">High (6M)</span>
          <span className="stat-value">{formatPrice(highPrice)}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Low (6M)</span>
          <span className="stat-value">{formatPrice(lowPrice)}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Avg Daily Volume</span>
          <span className="stat-value">{formatVolume(avgVolumeUSD / priceData[0].price, priceData[0].price)}</span>
        </div>
      </div>
    </div>
  )
}

export default AssetPage 