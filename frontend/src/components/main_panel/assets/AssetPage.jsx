import React, { useState, useEffect, useRef, useCallback } from 'react'
import OrderBook from './OrderBook'
import PriceChart from './PriceChart'
import chartDataManager from '../../../services/ChartDataManager'
import { uiStateManager } from '../../../services/uiStateManager'
import './AssetPage.css'

const AssetPage = ({ symbol = 'BTC', quoteAsset = 'USD', interval: initialInterval = '1h' }) => {
  const [priceData, setPriceData] = useState(null)
  const [currentPrice, setCurrentPrice] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [priceFlash, setPriceFlash] = useState(false)
  const [interval, setInterval] = useState(initialInterval)
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [userTrades, setUserTrades] = useState([])
  
  // Use refs to track active requests
  const abortControllerRef = useRef(null)
  const currentPriceIntervalRef = useRef(null)

  // Available intervals from ChartDataManager
  const availableIntervals = chartDataManager.getAvailableIntervals()

  // Cleanup function for intervals and requests
  const cleanup = useCallback(() => {
    if (currentPriceIntervalRef.current) {
      clearInterval(currentPriceIntervalRef.current)
      currentPriceIntervalRef.current = null
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
  }, [])

  useEffect(() => {
    fetchPriceData()
    fetchUserTrades()
    
    return cleanup
  }, [symbol, quoteAsset, interval, cleanup])

  useEffect(() => {
    // Set up periodic refresh
    let refreshInterval;
    
    if (interval === '5m') {
      // Refresh every 10 seconds for 5m data
      refreshInterval = setInterval(() => {
        fetchPriceData(true) // silent update
      }, 10000)
    } else {
      // Refresh current price every 5 seconds for other views
      refreshInterval = setInterval(() => {
        fetchCurrentPrice()
      }, 5000)
    }
    
    currentPriceIntervalRef.current = refreshInterval

    return () => {
      if (refreshInterval) clearInterval(refreshInterval)
    }
  }, [symbol, quoteAsset, interval])

  const fetchCurrentPrice = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/assets/${symbol}/current?quote=${quoteAsset}`)
      
      // Handle invalid symbol
      if (response.status === 404) {
        setError(`Symbol "${symbol}/${quoteAsset}" not found`)
        // Clear the interval to stop retrying
        if (currentPriceIntervalRef.current) {
          clearInterval(currentPriceIntervalRef.current)
          currentPriceIntervalRef.current = null
        }
        return
      }
      
      if (!response.ok) throw new Error('Failed to fetch current price')
      const data = await response.json()
      
      // Check if price changed
      if (currentPrice && data.price !== currentPrice.price) {
        setPriceFlash(true)
        setTimeout(() => setPriceFlash(false), 500)
      }
      
      setCurrentPrice(data)
      setLastUpdate(new Date())
      // Clear any previous errors
      setError(null)
    } catch (err) {
      console.error('Error fetching current price:', err)
      // Don't set error here for network issues, just log
    }
  }

  const fetchPriceData = async (silentUpdate = false) => {
    // Cancel any pending requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    // Create new abort controller
    abortControllerRef.current = new AbortController()

    if (!silentUpdate) {
      setIsTransitioning(true)
    }
    
    try {
      // Fetch current price first
      await fetchCurrentPrice()
      
      // If we already have an error from fetchCurrentPrice (invalid symbol), don't continue
      if (error) {
        return
      }

      // Calculate preload range based on interval
      const now = Date.now()
      const preloadRange = chartDataManager.getPreloadRange(now, interval)
      
      // Load data using ChartDataManager with intelligent caching
      const data = await chartDataManager.loadDataRange(
        symbol,
        preloadRange.start,
        preloadRange.end,
        interval
      )

      if (data && data.length > 0) {
        setPriceData(data)
        // Set initial visible range (last 30x intervals)
        const initialVisible = chartDataManager.getInitialVisibleRange(interval)
        console.log(`Loaded ${data.length} data points for ${symbol} with ${interval} interval`)
        console.log(`Initial visible range: ${initialVisible.bars} bars`)
      } else {
        console.error('No data received from ChartDataManager')
        setError('No data available for this symbol/interval combination')
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message)
        console.error('Error fetching price data:', err)
      }
    } finally {
      if (!silentUpdate) {
        setLoading(false)
        setIsTransitioning(false)
      }
    }
  }

  const fetchUserTrades = async () => {
    try {
      // Calculate days based on interval for user trades
      const intervalToDays = {
        '5m': 1,   // Show 1 day of trades for 5m interval
        '1h': 7,   // Show 7 days of trades for 1h interval
        '1d': 180  // Show 180 days of trades for 1d interval
      }
      const days = intervalToDays[interval] || 7
      
      const response = await fetch(
        `http://localhost:8000/api/assets/${symbol}/user-trades?days=${days}&quote=${quoteAsset}`
      )
      
      if (response.ok) {
        const data = await response.json()
        setUserTrades(data.trades || [])
      } else {
        // Don't show error for user trades, just log it
        console.error('Failed to fetch user trades:', response.status)
        setUserTrades([])
      }
    } catch (err) {
      console.error('Error fetching user trades:', err)
      setUserTrades([])
    }
  }

  const handleIntervalChange = (newInterval) => {
    if (newInterval === interval) return
    
    setInterval(newInterval)
    console.log(`Interval changed to: ${newInterval}`)
  }

  const handleSymbolClick = (newSymbol) => {
    // Dispatch a UI action to show the new symbol
    uiStateManager.dispatch({
      action: 'render_component',
      component: 'AssetPage',
      props: {
        symbol: newSymbol,
        quoteAsset: 'USD',
        interval: '1h'
      },
      target: 'main_panel'
    })
  }

  if (loading && !priceData) {
    return (
      <div className="asset-page">
        <div className="loading">Loading {symbol} data...</div>
      </div>
    )
  }

  if (error && !priceData) {
    return (
      <div className="asset-page">
        <div className="error-container">
          <h2>Symbol Not Found</h2>
          <p className="error-message">{error}</p>
          {error.includes('not found') && (
            <div className="suggestions">
              <p>Try one of these popular symbols:</p>
              <div className="symbol-suggestions">
                <button onClick={() => handleSymbolClick('BTC')} className="symbol-btn">BTC</button>
                <button onClick={() => handleSymbolClick('ETH')} className="symbol-btn">ETH</button>
                <button onClick={() => handleSymbolClick('SOL')} className="symbol-btn">SOL</button>
                <button onClick={() => handleSymbolClick('ARB')} className="symbol-btn">ARB</button>
                <button onClick={() => handleSymbolClick('MATIC')} className="symbol-btn">MATIC</button>
              </div>
              <p className="note">Note: Hyperliquid does not trade its own token (HYP) on the platform.</p>
            </div>
          )}
        </div>
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
        <h1>{symbol}/{quoteAsset}</h1>
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

      <div className="interval-selector">
        {availableIntervals.map(range => (
          <button
            key={range}
            className={`interval-btn ${interval === range ? 'active' : ''}`}
            onClick={() => handleIntervalChange(range)}
          >
            {range}
          </button>
        ))}
      </div>

      <div className="chart-and-orderbook-container">
        <div className={`chart-container ${isTransitioning ? 'transitioning' : ''}`}>
          {priceData && (
            <PriceChart 
              priceData={priceData} 
              isLiveMode={interval === '5m'} 
              userTrades={userTrades}
              symbol={symbol}
              quoteAsset={quoteAsset}
              height={500}
              interval={interval}
            />
          )}
          {isTransitioning && (
            <div className="loading-overlay">
              <div className="loading-spinner"></div>
            </div>
          )}
        </div>
        <div className="orderbook-container">
          <OrderBook symbol={symbol} quoteAsset={quoteAsset} />
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