import React, { useState, useEffect, useRef, memo } from 'react'
import wsService from '../../../services/websocketService'
import './OrderBook.css'

const OrderBook = memo(({ symbol }) => {
  const [orderBook, setOrderBook] = useState({ bids: [], asks: [] })
  const [lastUpdate, setLastUpdate] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const subscriptionRef = useRef(null)

  useEffect(() => {
    // Connect to WebSocket and subscribe to order book updates
    const setupWebSocket = async () => {
      try {
        await wsService.connect()
        setIsConnected(true)
        
        // Subscribe to L2 book updates
        const subscriptionId = wsService.subscribe(
          'l2Book',
          {
            type: 'l2Book',
            coin: symbol.replace('-PERP', '').replace('-SPOT', '')
          },
          handleOrderBookUpdate
        )
        
        subscriptionRef.current = subscriptionId
        console.log(`[OrderBook] Subscribed to ${symbol} order book`)
      } catch (error) {
        console.error('[OrderBook] Failed to connect:', error)
        setIsConnected(false)
      }
    }

    setupWebSocket()

    // Cleanup on unmount or symbol change
    return () => {
      if (subscriptionRef.current) {
        wsService.unsubscribe(subscriptionRef.current)
        subscriptionRef.current = null
      }
    }
  }, [symbol])

  const handleOrderBookUpdate = (data) => {
    console.log('[OrderBook] Received update:', data)
    
    if (data.levels && Array.isArray(data.levels) && data.levels.length === 2) {
      const [bids, asks] = data.levels
      
      // Process and limit to 5 levels
      const processedBids = bids.slice(0, 5).map(level => ({
        price: parseFloat(level.px),
        size: parseFloat(level.sz),
        numOrders: level.n
      }))
      
      const processedAsks = asks.slice(0, 5).map(level => ({
        price: parseFloat(level.px),
        size: parseFloat(level.sz),
        numOrders: level.n
      }))
      
      setOrderBook({
        bids: processedBids,
        asks: processedAsks
      })
      
      setLastUpdate(new Date())
    }
  }

  const formatPrice = (price) => {
    return price.toFixed(2)
  }

  const formatSize = (size) => {
    if (size >= 1000) {
      return `${(size / 1000).toFixed(2)}K`
    }
    return size.toFixed(4)
  }

  const getMaxSize = () => {
    const allSizes = [...orderBook.bids, ...orderBook.asks].map(level => level.size)
    return Math.max(...allSizes, 1)
  }

  const maxSize = getMaxSize()

  return (
    <div className="order-book">
      <div className="order-book-header">
        <h3>Order Book</h3>
        <div className="connection-status">
          <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
          <span className="status-text">{isConnected ? 'Live' : 'Disconnected'}</span>
        </div>
      </div>
      
      {lastUpdate && (
        <div className="last-update">
          Last update: {lastUpdate.toLocaleTimeString()}
        </div>
      )}

      <div className="order-book-content">
        <div className="order-book-section asks-section">
          <div className="section-header">
            <span>Price (USD)</span>
            <span>Size</span>
          </div>
          <div className="order-levels">
            {orderBook.asks.length > 0 ? (
              [...orderBook.asks].reverse().map((ask, index) => (
                <div key={`ask-${index}`} className="order-level ask-level">
                  <div className="level-bar ask-bar" style={{ width: `${(ask.size / maxSize) * 100}%` }}></div>
                  <span className="price ask-price">${formatPrice(ask.price)}</span>
                  <span className="size">{formatSize(ask.size)}</span>
                </div>
              ))
            ) : (
              <div className="no-data">No asks</div>
            )}
          </div>
        </div>

        <div className="spread-indicator">
          {orderBook.bids.length > 0 && orderBook.asks.length > 0 && (
            <>
              <span className="spread-label">Spread:</span>
              <span className="spread-value">
                ${(orderBook.asks[0].price - orderBook.bids[0].price).toFixed(2)}
              </span>
              <span className="spread-percent">
                ({((orderBook.asks[0].price - orderBook.bids[0].price) / orderBook.bids[0].price * 100).toFixed(3)}%)
              </span>
            </>
          )}
        </div>

        <div className="order-book-section bids-section">
          <div className="order-levels">
            {orderBook.bids.length > 0 ? (
              orderBook.bids.map((bid, index) => (
                <div key={`bid-${index}`} className="order-level bid-level">
                  <div className="level-bar bid-bar" style={{ width: `${(bid.size / maxSize) * 100}%` }}></div>
                  <span className="price bid-price">${formatPrice(bid.price)}</span>
                  <span className="size">{formatSize(bid.size)}</span>
                </div>
              ))
            ) : (
              <div className="no-data">No bids</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}, (prevProps, nextProps) => {
  // Only re-render if symbol changes
  return prevProps.symbol === nextProps.symbol
})

OrderBook.displayName = 'OrderBook'

export default OrderBook 