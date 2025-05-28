import React, { useState, useEffect } from 'react'
import './OrderHistory.css'

const OrderHistory = ({ filter = 'all' }) => {
  const [historyData, setHistoryData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeFilter, setActiveFilter] = useState(filter)
  const [sortBy, setSortBy] = useState('date')
  const [sortOrder, setSortOrder] = useState('desc')

  useEffect(() => {
    fetchHistoryData()
  }, [activeFilter])

  const fetchHistoryData = async () => {
    try {
      // Mock data for now - in production this would call the actual API
      const mockData = {
        trades: [
          {
            id: '1001',
            timestamp: new Date().getTime() - 3600000,
            symbol: 'BTC',
            side: 'Buy',
            size: 0.1,
            price: 47500,
            total: 4750,
            fee: 2.38,
            pnl: 125.50,
            status: 'Filled',
            orderType: 'Market'
          },
          {
            id: '1002',
            timestamp: new Date().getTime() - 7200000,
            symbol: 'ETH',
            side: 'Buy',
            size: 2.5,
            price: 3200,
            total: 8000,
            fee: 4.00,
            pnl: null,
            status: 'Filled',
            orderType: 'Limit'
          },
          {
            id: '1003',
            timestamp: new Date().getTime() - 10800000,
            symbol: 'SOL',
            side: 'Sell',
            size: 50,
            price: 150,
            total: 7500,
            fee: 3.75,
            pnl: -25.00,
            status: 'Filled',
            orderType: 'Market'
          },
          {
            id: '1004',
            timestamp: new Date().getTime() - 14400000,
            symbol: 'BTC',
            side: 'Sell',
            size: 0.05,
            price: 47000,
            total: 2350,
            fee: 1.18,
            pnl: 75.00,
            status: 'Filled',
            orderType: 'Limit'
          },
          {
            id: '1005',
            timestamp: new Date().getTime() - 18000000,
            symbol: 'MATIC',
            side: 'Buy',
            size: 1000,
            price: 1.25,
            total: 1250,
            fee: 0.63,
            pnl: null,
            status: 'Cancelled',
            orderType: 'Limit'
          }
        ],
        summary: {
          totalTrades: 5,
          totalVolume: 23850,
          totalFees: 11.94,
          totalPnl: 175.50,
          winRate: 66.67
        }
      }

      // Apply filter
      let filteredTrades = mockData.trades
      if (activeFilter !== 'all') {
        filteredTrades = mockData.trades.filter(trade => {
          switch (activeFilter) {
            case 'buys':
              return trade.side === 'Buy'
            case 'sells':
              return trade.side === 'Sell'
            case 'filled':
              return trade.status === 'Filled'
            case 'cancelled':
              return trade.status === 'Cancelled'
            default:
              return true
          }
        })
      }

      setHistoryData({
        ...mockData,
        trades: filteredTrades
      })
      setLoading(false)
    } catch (err) {
      console.error('Error fetching history data:', err)
      setError('Failed to load trade history')
      setLoading(false)
    }
  }

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
  }

  const sortedTrades = historyData?.trades.sort((a, b) => {
    let aVal = a[sortBy]
    let bVal = b[sortBy]
    
    if (sortBy === 'timestamp') {
      aVal = a.timestamp
      bVal = b.timestamp
    }
    
    if (sortOrder === 'asc') {
      return aVal > bVal ? 1 : -1
    } else {
      return aVal < bVal ? 1 : -1
    }
  })

  if (loading) {
    return (
      <div className="order-history">
        <div className="loading">Loading trade history...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="order-history">
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

  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="order-history">
      <div className="history-header">
        <h1>Trade History</h1>
        <div className="header-actions">
          <button className="export-btn" onClick={() => console.log('Export trades')}>
            Export CSV
          </button>
        </div>
      </div>

      <div className="history-filters">
        <button 
          className={`filter-btn ${activeFilter === 'all' ? 'active' : ''}`}
          onClick={() => setActiveFilter('all')}
        >
          All Trades
        </button>
        <button 
          className={`filter-btn ${activeFilter === 'buys' ? 'active' : ''}`}
          onClick={() => setActiveFilter('buys')}
        >
          Buys Only
        </button>
        <button 
          className={`filter-btn ${activeFilter === 'sells' ? 'active' : ''}`}
          onClick={() => setActiveFilter('sells')}
        >
          Sells Only
        </button>
        <button 
          className={`filter-btn ${activeFilter === 'filled' ? 'active' : ''}`}
          onClick={() => setActiveFilter('filled')}
        >
          Filled
        </button>
        <button 
          className={`filter-btn ${activeFilter === 'cancelled' ? 'active' : ''}`}
          onClick={() => setActiveFilter('cancelled')}
        >
          Cancelled
        </button>
      </div>

      <div className="history-summary">
        <div className="summary-item">
          <span className="summary-label">Total Trades</span>
          <span className="summary-value">{historyData.summary.totalTrades}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Total Volume</span>
          <span className="summary-value">{formatCurrency(historyData.summary.totalVolume)}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Total Fees</span>
          <span className="summary-value">{formatCurrency(historyData.summary.totalFees)}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Total PnL</span>
          <span className={`summary-value ${historyData.summary.totalPnl >= 0 ? 'positive' : 'negative'}`}>
            {formatCurrency(historyData.summary.totalPnl)}
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Win Rate</span>
          <span className="summary-value">{historyData.summary.winRate}%</span>
        </div>
      </div>

      <div className="history-table">
        <div className="table-header">
          <div className="table-cell sortable" onClick={() => handleSort('timestamp')}>
            Date/Time {sortBy === 'timestamp' && (sortOrder === 'asc' ? '↑' : '↓')}
          </div>
          <div className="table-cell sortable" onClick={() => handleSort('symbol')}>
            Symbol {sortBy === 'symbol' && (sortOrder === 'asc' ? '↑' : '↓')}
          </div>
          <div className="table-cell">Side</div>
          <div className="table-cell">Type</div>
          <div className="table-cell sortable" onClick={() => handleSort('size')}>
            Size {sortBy === 'size' && (sortOrder === 'asc' ? '↑' : '↓')}
          </div>
          <div className="table-cell sortable" onClick={() => handleSort('price')}>
            Price {sortBy === 'price' && (sortOrder === 'asc' ? '↑' : '↓')}
          </div>
          <div className="table-cell sortable" onClick={() => handleSort('total')}>
            Total {sortBy === 'total' && (sortOrder === 'asc' ? '↑' : '↓')}
          </div>
          <div className="table-cell">Fee</div>
          <div className="table-cell sortable" onClick={() => handleSort('pnl')}>
            PnL {sortBy === 'pnl' && (sortOrder === 'asc' ? '↑' : '↓')}
          </div>
          <div className="table-cell">Status</div>
        </div>
        
        {sortedTrades.length === 0 ? (
          <div className="no-trades">No trades found</div>
        ) : (
          sortedTrades.map((trade) => (
            <div key={trade.id} className="table-row">
              <div className="table-cell date">{formatDate(trade.timestamp)}</div>
              <div className="table-cell symbol">{trade.symbol}</div>
              <div className={`table-cell side ${trade.side.toLowerCase()}`}>
                {trade.side}
              </div>
              <div className="table-cell">{trade.orderType}</div>
              <div className="table-cell">{trade.size}</div>
              <div className="table-cell">{formatCurrency(trade.price)}</div>
              <div className="table-cell">{formatCurrency(trade.total)}</div>
              <div className="table-cell fee">{formatCurrency(trade.fee)}</div>
              <div className={`table-cell pnl ${trade.pnl ? (trade.pnl >= 0 ? 'positive' : 'negative') : ''}`}>
                {trade.pnl ? formatCurrency(trade.pnl) : '-'}
              </div>
              <div className={`table-cell status ${trade.status.toLowerCase()}`}>
                {trade.status}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default OrderHistory 