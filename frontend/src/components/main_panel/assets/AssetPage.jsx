import React, { useState, useEffect, useRef, useCallback } from 'react'
import OrderBook from './OrderBook'
import PriceChart from './PriceChart'
import priceDataCache from '../../../services/priceDataCache'
import { uiStateManager } from '../../../services/uiStateManager'
import './AssetPage.css'

const AssetPage = ({ symbol = 'BTC', quoteAsset = 'USD', timeRange: initialTimeRange = '6M' }) => {
  const [priceData, setPriceData] = useState(null)
  const [currentPrice, setCurrentPrice] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [priceFlash, setPriceFlash] = useState(false)
  const [timeRange, setTimeRange] = useState(initialTimeRange)
  const [isLiveMode, setIsLiveMode] = useState(false)
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [userTrades, setUserTrades] = useState([])
  
  // Use refs to track active requests
  const abortControllerRef = useRef(null)
  const currentPriceIntervalRef = useRef(null)

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
  }, [symbol, quoteAsset, timeRange, cleanup])

  useEffect(() => {
    // Set up periodic refresh
    let interval;
    
    if (timeRange === 'Live') {
      // Refresh every 10 seconds for live data
      interval = setInterval(() => {
        fetchPriceData(true) // silent update
      }, 10000)
    } else {
      // Refresh current price every 5 seconds for other views
      interval = setInterval(() => {
        fetchCurrentPrice()
      }, 5000)
    }
    
    currentPriceIntervalRef.current = interval

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [symbol, quoteAsset, timeRange])

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
    // Check cache first
    const cachedData = priceDataCache.get(`${symbol}/${quoteAsset}`, timeRange, timeRange === 'Live')
    if (cachedData && !silentUpdate) {
      setPriceData(cachedData)
      setIsLiveMode(timeRange === 'Live')
      setLoading(false)
      // Still fetch current price
      fetchCurrentPrice()
      return
    }

    // Cancel any pending requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    // Create new abort controller
    abortControllerRef.current = new AbortController()
    const signal = abortControllerRef.current.signal

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

      if (timeRange === 'Live') {
        // Fetch live minute-level data
        setIsLiveMode(true)
        const liveResponse = await fetch(
          `http://localhost:8000/api/assets/${symbol}/live-data?minutes=30&quote=${quoteAsset}`,
          { signal }
        )
        
        // Handle invalid symbol for live data
        if (liveResponse.status === 404 || liveResponse.status === 500) {
          const errorData = await liveResponse.json()
          setError(errorData.detail || `Failed to fetch data for "${symbol}/${quoteAsset}"`)
          // Clear the interval to stop retrying
          if (currentPriceIntervalRef.current) {
            clearInterval(currentPriceIntervalRef.current)
            currentPriceIntervalRef.current = null
          }
          return
        }
        
        if (!liveResponse.ok) throw new Error('Failed to fetch live data')
        const liveData = await liveResponse.json()
        
        if (liveData && liveData.data && Array.isArray(liveData.data)) {
          setPriceData(liveData.data)
          priceDataCache.set(`${symbol}/${quoteAsset}`, timeRange, liveData.data, true)
        } else {
          console.error('Invalid live data format:', liveData)
          setError('Invalid data format received from server')
        }
      } else {
        // Fetch historical data
        setIsLiveMode(false)
        const days = timeRangeMap[timeRange] || 180
        const historyResponse = await fetch(
          `http://localhost:8000/api/assets/${symbol}/price-history?days=${days}&quote=${quoteAsset}`,
          { signal }
        )
        
        // Handle invalid symbol for historical data
        if (historyResponse.status === 404 || historyResponse.status === 500) {
          const errorData = await historyResponse.json()
          setError(errorData.detail || `Failed to fetch data for "${symbol}/${quoteAsset}"`)
          // Clear the interval to stop retrying
          if (currentPriceIntervalRef.current) {
            clearInterval(currentPriceIntervalRef.current)
            currentPriceIntervalRef.current = null
          }
          return
        }
        
        if (!historyResponse.ok) throw new Error('Failed to fetch price history')
        const historyData = await historyResponse.json()
        
        if (historyData && historyData.data && Array.isArray(historyData.data)) {
          setPriceData(historyData.data)
          priceDataCache.set(`${symbol}/${quoteAsset}`, timeRange, historyData.data, false)
        } else {
          console.error('Invalid price data format:', historyData)
          setError('Invalid data format received from server')
        }
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
      const days = timeRangeMap[timeRange] || 180
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

  const handleTimeRangeChange = (newTimeRange) => {
    if (newTimeRange === timeRange) return
    
    setTimeRange(newTimeRange)
    console.log(`Time range changed to: ${newTimeRange}`)
  }

  const handleSymbolClick = (newSymbol) => {
    // Dispatch a UI action to show the new symbol
    uiStateManager.dispatch({
      action: 'render_component',
      component: 'AssetPage',
      props: {
        symbol: newSymbol,
        quoteAsset: 'USD',
        timeRange: '6M'
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

      <div className="time-range-selector">
        {Object.keys(timeRangeMap).map(range => (
          <button
            key={range}
            className={`time-range-btn ${timeRange === range ? 'active' : ''}`}
            onClick={() => handleTimeRangeChange(range)}
          >
            {range}
          </button>
        ))}
      </div>

      {userTrades.length > 0 && (
        <div className="trade-legend">
          <span className="legend-item">
            <span className="legend-dot buy"></span>
            Buy
          </span>
          <span className="legend-item">
            <span className="legend-dot sell"></span>
            Sell
          </span>
          <span className="legend-info">
            ({userTrades.length} trades in this period)
          </span>
        </div>
      )}

      <div className="chart-and-orderbook-container">
        <div className={`chart-container ${isTransitioning ? 'transitioning' : ''}`}>
          {priceData && <PriceChart priceData={priceData} isLiveMode={isLiveMode} userTrades={userTrades} />}
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