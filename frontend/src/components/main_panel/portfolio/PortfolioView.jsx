import React, { useState, useEffect } from 'react'
import './PortfolioView.css'

const PortfolioView = () => {
  const [portfolioData, setPortfolioData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchPortfolioData()
    // Refresh every 10 seconds
    const interval = setInterval(fetchPortfolioData, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchPortfolioData = async () => {
    try {
      // For now, we'll use mock data since the backend endpoint isn't implemented yet
      // In production, this would call the actual API endpoint
      const mockData = {
        totalEquity: 10000.00,
        availableBalance: 5000.00,
        marginUsed: 5000.00,
        unrealizedPnl: 250.50,
        realizedPnl: 1250.75,
        positions: [
          {
            symbol: 'BTC',
            side: 'Long',
            size: 0.1,
            entryPrice: 45000,
            markPrice: 47500,
            pnl: 250.00,
            pnlPercent: 5.56
          },
          {
            symbol: 'ETH',
            side: 'Long',
            size: 2.5,
            entryPrice: 3200,
            markPrice: 3210,
            pnl: 25.00,
            pnlPercent: 0.31
          },
          {
            symbol: 'SOL',
            side: 'Short',
            size: 50,
            entryPrice: 150,
            markPrice: 149.50,
            pnl: 25.00,
            pnlPercent: 0.33
          }
        ]
      }
      
      setPortfolioData(mockData)
      setLoading(false)
    } catch (err) {
      console.error('Error fetching portfolio data:', err)
      setError('Failed to load portfolio data')
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="portfolio-view">
        <div className="loading">Loading portfolio...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="portfolio-view">
        <div className="error">{error}</div>
      </div>
    )
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value)
  }

  const formatPercent = (value) => {
    const sign = value >= 0 ? '+' : ''
    return `${sign}${value.toFixed(2)}%`
  }

  return (
    <div className="portfolio-view">
      <div className="portfolio-header">
        <h1>Portfolio Overview</h1>
        <div className="last-update">
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>

      <div className="portfolio-summary">
        <div className="summary-card">
          <div className="summary-label">Total Equity</div>
          <div className="summary-value">{formatCurrency(portfolioData.totalEquity)}</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Available Balance</div>
          <div className="summary-value">{formatCurrency(portfolioData.availableBalance)}</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Margin Used</div>
          <div className="summary-value">{formatCurrency(portfolioData.marginUsed)}</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Unrealized PnL</div>
          <div className={`summary-value ${portfolioData.unrealizedPnl >= 0 ? 'positive' : 'negative'}`}>
            {formatCurrency(portfolioData.unrealizedPnl)}
          </div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Realized PnL</div>
          <div className={`summary-value ${portfolioData.realizedPnl >= 0 ? 'positive' : 'negative'}`}>
            {formatCurrency(portfolioData.realizedPnl)}
          </div>
        </div>
      </div>

      <div className="positions-section">
        <h2>Open Positions</h2>
        {portfolioData.positions.length === 0 ? (
          <div className="no-positions">No open positions</div>
        ) : (
          <div className="positions-table">
            <div className="table-header">
              <div className="table-cell">Symbol</div>
              <div className="table-cell">Side</div>
              <div className="table-cell">Size</div>
              <div className="table-cell">Entry Price</div>
              <div className="table-cell">Mark Price</div>
              <div className="table-cell">PnL</div>
              <div className="table-cell">PnL %</div>
              <div className="table-cell">Actions</div>
            </div>
            {portfolioData.positions.map((position, index) => (
              <div key={index} className="table-row">
                <div className="table-cell symbol">{position.symbol}</div>
                <div className={`table-cell side ${position.side.toLowerCase()}`}>
                  {position.side}
                </div>
                <div className="table-cell">{position.size}</div>
                <div className="table-cell">{formatCurrency(position.entryPrice)}</div>
                <div className="table-cell">{formatCurrency(position.markPrice)}</div>
                <div className={`table-cell pnl ${position.pnl >= 0 ? 'positive' : 'negative'}`}>
                  {formatCurrency(position.pnl)}
                </div>
                <div className={`table-cell pnl-percent ${position.pnlPercent >= 0 ? 'positive' : 'negative'}`}>
                  {formatPercent(position.pnlPercent)}
                </div>
                <div className="table-cell actions">
                  <button className="close-btn" onClick={() => console.log('Close position:', position.symbol)}>
                    Close
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="portfolio-actions">
        <button className="action-btn primary" onClick={() => console.log('Open trade form')}>
          New Trade
        </button>
        <button className="action-btn secondary" onClick={() => console.log('View history')}>
          Trade History
        </button>
        <button className="action-btn secondary" onClick={fetchPortfolioData}>
          Refresh
        </button>
      </div>
    </div>
  )
}

export default PortfolioView 