/**
 * ChartDataManager - Handles efficient data loading and caching for TradingView charts
 * 
 * Features:
 * - Chunked data loading for infinite scroll
 * - Multi-level caching (memory + IndexedDB)
 * - Automatic cache invalidation
 * - Request deduplication
 * - Efficient memory management
 */

import { openDB } from 'idb';

class ChartDataManager {
  constructor() {
    // Configuration
    this.config = {
      chunkSize: 1000,              // Number of candles per chunk
      maxMemoryChunks: 20,          // Maximum chunks to keep in memory
      cacheExpirationMs: 300000,    // 5 minutes for historical data
      liveCacheExpirationMs: 5000,  // 5 seconds for live data
      prefetchThreshold: 200,       // Start loading when this many candles from edge
      maxConcurrentRequests: 2,     // Limit concurrent API requests
    };

    // Memory cache
    this.memoryCache = new Map();
    this.cacheMetadata = new Map();
    
    // Request management
    this.pendingRequests = new Map();
    this.activeRequests = 0;
    
    // IndexedDB setup
    this.dbName = 'HyperliquidChartData';
    this.dbVersion = 1;
    this.db = null;
    this.initDB();

    // Cache statistics
    this.stats = {
      hits: 0,
      misses: 0,
      apiCalls: 0,
      bytesLoaded: 0,
    };
  }

  async initDB() {
    try {
      this.db = await openDB(this.dbName, this.dbVersion, {
        upgrade(db) {
          // Create object stores for different data types
          if (!db.objectStoreNames.contains('priceData')) {
            const priceStore = db.createObjectStore('priceData', { 
              keyPath: 'id' 
            });
            priceStore.createIndex('symbol', 'symbol');
            priceStore.createIndex('timestamp', 'timestamp');
            priceStore.createIndex('expiry', 'expiry');
          }

          if (!db.objectStoreNames.contains('metadata')) {
            db.createObjectStore('metadata', { keyPath: 'key' });
          }
        },
      });
    } catch (error) {
      console.error('Failed to initialize IndexedDB:', error);
      // Fall back to memory-only caching
      this.db = null;
    }
  }

  /**
   * Get chunk key for caching
   */
  getChunkKey(symbol, startTime, endTime, interval) {
    return `${symbol}_${interval}_${startTime}_${endTime}`;
  }

  /**
   * Load data for a specific time range
   */
  async loadDataRange(symbol, startTime, endTime, interval = '1h') {
    const chunks = this.calculateRequiredChunks(startTime, endTime, interval);
    const results = [];

    for (const chunk of chunks) {
      const data = await this.loadChunk(symbol, chunk.start, chunk.end, interval);
      if (data) {
        results.push(...data);
      }
    }

    // Sort and deduplicate
    return this.processResults(results);
  }

  /**
   * Calculate which chunks are needed for a time range
   */
  calculateRequiredChunks(startTime, endTime, interval) {
    const chunks = [];
    const chunkDuration = this.getChunkDuration(interval);
    
    let currentStart = Math.floor(startTime / chunkDuration) * chunkDuration;
    
    while (currentStart < endTime) {
      const currentEnd = Math.min(currentStart + chunkDuration, endTime);
      chunks.push({
        start: currentStart,
        end: currentEnd,
      });
      currentStart = currentEnd;
    }

    return chunks;
  }

  /**
   * Get chunk duration based on interval
   */
  getChunkDuration(interval) {
    const durations = {
      '1m': 3600 * 1000,        // 1 hour in ms
      '5m': 12 * 3600 * 1000,   // 12 hours
      '15m': 24 * 3600 * 1000,  // 1 day
      '1h': 7 * 24 * 3600 * 1000, // 1 week
      '4h': 30 * 24 * 3600 * 1000, // 1 month
      '1d': 365 * 24 * 3600 * 1000, // 1 year
    };
    return durations[interval] || durations['1h'];
  }

  /**
   * Load a single chunk of data
   */
  async loadChunk(symbol, startTime, endTime, interval) {
    const chunkKey = this.getChunkKey(symbol, startTime, endTime, interval);

    // Check memory cache first
    const memoryData = await this.getFromMemoryCache(chunkKey);
    if (memoryData) {
      this.stats.hits++;
      return memoryData;
    }

    // Check IndexedDB cache
    const dbData = await this.getFromDBCache(chunkKey);
    if (dbData) {
      this.stats.hits++;
      // Promote to memory cache
      this.setMemoryCache(chunkKey, dbData);
      return dbData;
    }

    // Check if request is already pending
    if (this.pendingRequests.has(chunkKey)) {
      return this.pendingRequests.get(chunkKey);
    }

    // Load from API
    this.stats.misses++;
    const promise = this.loadFromAPI(symbol, startTime, endTime, interval, chunkKey);
    this.pendingRequests.set(chunkKey, promise);

    try {
      const data = await promise;
      this.pendingRequests.delete(chunkKey);
      return data;
    } catch (error) {
      this.pendingRequests.delete(chunkKey);
      throw error;
    }
  }

  /**
   * Get data from memory cache
   */
  async getFromMemoryCache(key) {
    const cached = this.memoryCache.get(key);
    if (!cached) return null;

    const metadata = this.cacheMetadata.get(key);
    if (!metadata || Date.now() > metadata.expiry) {
      this.memoryCache.delete(key);
      this.cacheMetadata.delete(key);
      return null;
    }

    return cached;
  }

  /**
   * Get data from IndexedDB cache
   */
  async getFromDBCache(key) {
    if (!this.db) return null;

    try {
      const tx = this.db.transaction(['priceData'], 'readonly');
      const store = tx.objectStore('priceData');
      const record = await store.get(key);

      if (!record || Date.now() > record.expiry) {
        // Expired, delete it
        if (record) {
          const deleteTx = this.db.transaction(['priceData'], 'readwrite');
          await deleteTx.objectStore('priceData').delete(key);
        }
        return null;
      }

      return record.data;
    } catch (error) {
      console.error('IndexedDB read error:', error);
      return null;
    }
  }

  /**
   * Set memory cache with LRU eviction
   */
  setMemoryCache(key, data) {
    // Implement LRU eviction
    if (this.memoryCache.size >= this.config.maxMemoryChunks) {
      const oldestKey = this.memoryCache.keys().next().value;
      this.memoryCache.delete(oldestKey);
      this.cacheMetadata.delete(oldestKey);
    }

    this.memoryCache.set(key, data);
    this.cacheMetadata.set(key, {
      expiry: Date.now() + this.config.cacheExpirationMs,
      size: JSON.stringify(data).length,
    });
  }

  /**
   * Save to IndexedDB cache
   */
  async saveToDBCache(key, data, symbol) {
    if (!this.db) return;

    try {
      const tx = this.db.transaction(['priceData'], 'readwrite');
      const store = tx.objectStore('priceData');
      
      await store.put({
        id: key,
        symbol: symbol,
        data: data,
        timestamp: Date.now(),
        expiry: Date.now() + this.config.cacheExpirationMs,
      });
    } catch (error) {
      console.error('IndexedDB write error:', error);
    }
  }

  /**
   * Load data from API with rate limiting
   */
  async loadFromAPI(symbol, startTime, endTime, interval, chunkKey) {
    // Wait if too many concurrent requests
    while (this.activeRequests >= this.config.maxConcurrentRequests) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    this.activeRequests++;
    this.stats.apiCalls++;

    try {
      // Calculate the appropriate endpoint and parameters
      const days = (endTime - startTime) / (24 * 3600 * 1000);
      
      const response = await fetch(
        `http://localhost:8000/api/assets/${symbol}/price-history?days=${Math.ceil(days)}&quote=USD`
      );

      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`);
      }

      const result = await response.json();
      const data = result.data || [];

      // Filter data to match requested time range
      const filteredData = data.filter(item => {
        const timestamp = item.timestamp || new Date(item.date).getTime();
        return timestamp >= startTime && timestamp <= endTime;
      });

      // Update statistics
      this.stats.bytesLoaded += JSON.stringify(filteredData).length;

      // Cache the data
      this.setMemoryCache(chunkKey, filteredData);
      await this.saveToDBCache(chunkKey, filteredData, symbol);

      return filteredData;
    } finally {
      this.activeRequests--;
    }
  }

  /**
   * Process and deduplicate results
   */
  processResults(results) {
    const seen = new Set();
    const processed = [];

    for (const item of results) {
      const key = `${item.timestamp || item.time}`;
      if (!seen.has(key)) {
        seen.add(key);
        processed.push(item);
      }
    }

    // Sort by timestamp
    return processed.sort((a, b) => {
      const timeA = a.timestamp || new Date(a.time).getTime();
      const timeB = b.timestamp || new Date(b.time).getTime();
      return timeA - timeB;
    });
  }

  /**
   * Prefetch adjacent chunks
   */
  async prefetchAdjacent(symbol, currentStart, currentEnd, interval) {
    const chunkDuration = this.getChunkDuration(interval);
    
    // Prefetch previous chunk
    const prevStart = currentStart - chunkDuration;
    const prevEnd = currentStart;
    this.loadChunk(symbol, prevStart, prevEnd, interval).catch(() => {});

    // Prefetch next chunk
    const nextStart = currentEnd;
    const nextEnd = currentEnd + chunkDuration;
    this.loadChunk(symbol, nextStart, nextEnd, interval).catch(() => {});
  }

  /**
   * Clear cache for a symbol
   */
  async clearSymbolCache(symbol) {
    // Clear memory cache
    for (const [key] of this.memoryCache) {
      if (key.startsWith(symbol)) {
        this.memoryCache.delete(key);
        this.cacheMetadata.delete(key);
      }
    }

    // Clear IndexedDB cache
    if (this.db) {
      try {
        const tx = this.db.transaction(['priceData'], 'readwrite');
        const store = tx.objectStore('priceData');
        const index = store.index('symbol');
        
        const keys = await index.getAllKeys(symbol);
        for (const key of keys) {
          await store.delete(key);
        }
      } catch (error) {
        console.error('Failed to clear IndexedDB cache:', error);
      }
    }
  }

  /**
   * Get cache statistics
   */
  getStats() {
    return {
      ...this.stats,
      memoryCacheSize: this.memoryCache.size,
      hitRate: this.stats.hits / (this.stats.hits + this.stats.misses) || 0,
    };
  }

  /**
   * Clean up expired cache entries
   */
  async cleanupExpiredCache() {
    // Clean memory cache
    const now = Date.now();
    for (const [key, metadata] of this.cacheMetadata) {
      if (now > metadata.expiry) {
        this.memoryCache.delete(key);
        this.cacheMetadata.delete(key);
      }
    }

    // Clean IndexedDB cache
    if (this.db) {
      try {
        const tx = this.db.transaction(['priceData'], 'readwrite');
        const store = tx.objectStore('priceData');
        const index = store.index('expiry');
        
        const range = IDBKeyRange.upperBound(now);
        const keys = await index.getAllKeys(range);
        
        for (const key of keys) {
          await store.delete(key);
        }
      } catch (error) {
        console.error('Failed to cleanup IndexedDB:', error);
      }
    }
  }
}

// Create singleton instance
export const chartDataManager = new ChartDataManager();

// Set up periodic cleanup
setInterval(() => {
  chartDataManager.cleanupExpiredCache();
}, 60000); // Run every minute

export default chartDataManager; 