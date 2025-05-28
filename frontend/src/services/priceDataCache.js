class PriceDataCache {
  constructor() {
    this.cache = new Map()
    this.cacheTimeout = 60000 // 1 minute for historical data
    this.liveCacheTimeout = 5000 // 5 seconds for live data
  }

  getCacheKey(symbol, timeRange, isLive = false) {
    return `${symbol}-${timeRange}-${isLive ? 'live' : 'historical'}`
  }

  get(symbol, timeRange, isLive = false) {
    const key = this.getCacheKey(symbol, timeRange, isLive)
    const cached = this.cache.get(key)
    
    if (!cached) return null
    
    const timeout = isLive ? this.liveCacheTimeout : this.cacheTimeout
    const isExpired = Date.now() - cached.timestamp > timeout
    
    if (isExpired) {
      this.cache.delete(key)
      return null
    }
    
    return cached.data
  }

  set(symbol, timeRange, data, isLive = false) {
    const key = this.getCacheKey(symbol, timeRange, isLive)
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    })
  }

  clear(symbol = null) {
    if (symbol) {
      // Clear all entries for a specific symbol
      for (const [key] of this.cache) {
        if (key.startsWith(symbol)) {
          this.cache.delete(key)
        }
      }
    } else {
      // Clear entire cache
      this.cache.clear()
    }
  }

  // Get cache stats for debugging
  getStats() {
    const stats = {
      size: this.cache.size,
      entries: []
    }
    
    for (const [key, value] of this.cache) {
      stats.entries.push({
        key,
        age: Date.now() - value.timestamp,
        dataPoints: value.data?.length || 0
      })
    }
    
    return stats
  }
}

// Create singleton instance
const priceDataCache = new PriceDataCache()

export default priceDataCache 