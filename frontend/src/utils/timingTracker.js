/**
 * Frontend timing tracker for measuring latency on the client side.
 */

class FrontendTimingTracker {
  constructor() {
    this.timings = new Map();
    this.requestMetadata = new Map();
  }

  /**
   * Start timing a request
   * @param {string} requestId - Unique request identifier
   * @param {object} metadata - Additional metadata about the request
   * @returns {string} The request ID
   */
  startRequest(requestId, metadata = {}) {
    const timing = {
      id: requestId,
      startTime: performance.now(),
      stages: new Map(),
      metadata: {
        ...metadata,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString()
      }
    };
    
    this.timings.set(requestId, timing);
    console.log(`[Timing] Started tracking request: ${requestId}`);
    return requestId;
  }

  /**
   * Start timing a specific stage
   * @param {string} requestId - Request identifier
   * @param {string} stage - Stage name
   */
  startStage(requestId, stage) {
    const timing = this.timings.get(requestId);
    if (!timing) {
      console.warn(`[Timing] Request ${requestId} not found`);
      return;
    }
    
    timing.stages.set(stage, {
      startTime: performance.now()
    });
    console.log(`[Timing] Started stage '${stage}' for request ${requestId}`);
  }

  /**
   * End timing a specific stage
   * @param {string} requestId - Request identifier
   * @param {string} stage - Stage name
   * @param {object} metadata - Additional stage metadata
   */
  endStage(requestId, stage, metadata = {}) {
    const timing = this.timings.get(requestId);
    if (!timing || !timing.stages.has(stage)) {
      console.warn(`[Timing] Stage '${stage}' not found for request ${requestId}`);
      return;
    }
    
    const stageData = timing.stages.get(stage);
    const endTime = performance.now();
    stageData.endTime = endTime;
    stageData.duration = endTime - stageData.startTime;
    stageData.metadata = metadata;
    
    console.log(`[Timing] Ended stage '${stage}' for request ${requestId}: ${stageData.duration.toFixed(2)}ms`);
  }

  /**
   * End timing a request
   * @param {string} requestId - Request identifier
   * @param {object} metadata - Additional end metadata
   */
  endRequest(requestId, metadata = {}) {
    const timing = this.timings.get(requestId);
    if (!timing) {
      console.warn(`[Timing] Request ${requestId} not found`);
      return;
    }
    
    timing.endTime = performance.now();
    timing.totalDuration = timing.endTime - timing.startTime;
    timing.endMetadata = metadata;
    
    console.log(`[Timing] Ended request ${requestId}: Total duration ${timing.totalDuration.toFixed(2)}ms`);
    
    // Log detailed breakdown
    this.logBreakdown(requestId);
    
    // Send timing data to backend
    this.sendToBackend(requestId);
  }

  /**
   * Get timing summary for a request
   * @param {string} requestId - Request identifier
   * @returns {object} Timing summary
   */
  getSummary(requestId) {
    const timing = this.timings.get(requestId);
    if (!timing) return null;
    
    const stages = {};
    timing.stages.forEach((stage, name) => {
      stages[name] = {
        duration: stage.duration,
        metadata: stage.metadata
      };
    });
    
    return {
      requestId,
      totalDuration: timing.totalDuration,
      stages,
      metadata: timing.metadata,
      endMetadata: timing.endMetadata
    };
  }

  /**
   * Log timing breakdown to console
   * @param {string} requestId - Request identifier
   */
  logBreakdown(requestId) {
    const summary = this.getSummary(requestId);
    if (!summary) return;
    
    console.group(`[Timing] Breakdown for request ${requestId}`);
    console.log(`Total Duration: ${summary.totalDuration.toFixed(2)}ms`);
    console.log('Stages:');
    
    Object.entries(summary.stages).forEach(([stage, data]) => {
      const percentage = (data.duration / summary.totalDuration * 100).toFixed(1);
      console.log(`  ${stage}: ${data.duration.toFixed(2)}ms (${percentage}%)`);
    });
    
    console.groupEnd();
  }

  /**
   * Send timing data to backend
   * @param {string} requestId - Request identifier
   */
  async sendToBackend(requestId) {
    const summary = this.getSummary(requestId);
    if (!summary) return;
    
    try {
      // Send frontend timing data to backend
      const response = await fetch('/api/timing/frontend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Request-ID': requestId
        },
        body: JSON.stringify({
          ...summary,
          source: 'frontend'
        })
      });
      
      if (!response.ok) {
        console.error(`[Timing] Failed to send timing data to backend: ${response.status}`);
      }
    } catch (error) {
      console.error('[Timing] Error sending timing data to backend:', error);
    }
  }

  /**
   * Clear timing data for a request
   * @param {string} requestId - Request identifier
   */
  clear(requestId) {
    this.timings.delete(requestId);
    this.requestMetadata.delete(requestId);
  }

  /**
   * Clear all timing data
   */
  clearAll() {
    this.timings.clear();
    this.requestMetadata.clear();
  }
}

// Create singleton instance
const timingTracker = new FrontendTimingTracker();

// Helper function to generate request ID
export function generateRequestId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// Export the tracker instance
export default timingTracker; 