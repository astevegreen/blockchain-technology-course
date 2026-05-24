/**
 * EventIndexer - Incremental event caching with memory limits
 * 
 * This class manages cached blockchain events, enabling incremental fetching
 * to avoid repeatedly querying from block 0. It maintains a memory-efficient
 * cache with configurable limits.
 */

export class EventIndexer {
  /**
   * Create a new EventIndexer
   * @param {Object} options - Configuration options
   * @param {number} options.maxEventsPerType - Maximum events to keep per type (default: 1000)
   * @param {boolean} options.persistToStorage - Whether to persist to localStorage (default: false)
   * @param {string} options.storageKey - Key for localStorage (default: 'event_index')
   */
  constructor(options = {}) {
    this.maxEventsPerType = options.maxEventsPerType ?? 1000;
    this.persistToStorage = options.persistToStorage ?? false;
    this.storageKey = options.storageKey ?? 'event_index';
    
    // Map of eventName -> { lastBlock: number, events: Array }
    this.cache = new Map();
    
    // Load from storage if persistence is enabled
    if (this.persistToStorage) {
      this._loadFromStorage();
    }
  }

  /**
   * Get the last processed block for an event type
   * @param {string} eventName - The event type
   * @returns {number} - Last processed block (0 if never processed)
   */
  getLastBlock(eventName) {
    const cached = this.cache.get(eventName);
    return cached?.lastBlock ?? 0;
  }

  /**
   * Get all cached events for an event type
   * @param {string} eventName - The event type
   * @returns {Array} - Cached events
   */
  getEvents(eventName) {
    return this.cache.get(eventName)?.events ?? [];
  }

  /**
   * Append new events to the cache
   * @param {string} eventName - The event type
   * @param {Array} newEvents - New events to append
   * @param {number} toBlock - The block number these events were fetched up to
   * @returns {Array} - All cached events for this type
   */
  appendEvents(eventName, newEvents, toBlock) {
    const existing = this.cache.get(eventName) || { lastBlock: 0, events: [] };
    
    // Append new events
    existing.events.push(...newEvents);
    existing.lastBlock = toBlock;
    
    // Trim to max size (keep most recent)
    if (existing.events.length > this.maxEventsPerType) {
      existing.events = existing.events.slice(-this.maxEventsPerType);
    }
    
    this.cache.set(eventName, existing);
    
    // Persist if enabled
    if (this.persistToStorage) {
      this._saveToStorage();
    }
    
    return existing.events;
  }

  /**
   * Set events directly (replaces existing)
   * @param {string} eventName - The event type
   * @param {Array} events - Events to set
   * @param {number} toBlock - The block number
   */
  setEvents(eventName, events, toBlock) {
    // Trim to max size
    const trimmed = events.length > this.maxEventsPerType 
      ? events.slice(-this.maxEventsPerType)
      : events;
    
    this.cache.set(eventName, { lastBlock: toBlock, events: trimmed });
    
    if (this.persistToStorage) {
      this._saveToStorage();
    }
  }

  /**
   * Check if we have any cached events for a type
   * @param {string} eventName - The event type
   * @returns {boolean}
   */
  hasEvents(eventName) {
    const cached = this.cache.get(eventName);
    return cached && cached.events.length > 0;
  }

  /**
   * Get the count of cached events for a type
   * @param {string} eventName - The event type
   * @returns {number}
   */
  getEventCount(eventName) {
    return this.cache.get(eventName)?.events?.length ?? 0;
  }

  /**
   * Clear cache for a specific event type
   * @param {string} eventName - The event type
   */
  clearEventType(eventName) {
    this.cache.delete(eventName);
    
    if (this.persistToStorage) {
      this._saveToStorage();
    }
  }

  /**
   * Clear all cached events
   */
  clear() {
    this.cache.clear();
    
    if (this.persistToStorage) {
      try {
        localStorage.removeItem(this.storageKey);
      } catch (e) {
        // localStorage may not be available
      }
    }
  }

  /**
   * Get a summary of the cache state
   * @returns {Object} - Cache statistics
   */
  getStats() {
    const stats = {
      eventTypes: this.cache.size,
      totalEvents: 0,
      byType: {}
    };
    
    for (const [name, data] of this.cache) {
      stats.byType[name] = {
        count: data.events.length,
        lastBlock: data.lastBlock
      };
      stats.totalEvents += data.events.length;
    }
    
    return stats;
  }

  /**
   * Export cache to a plain object (for debugging/serialization)
   * @returns {Object}
   */
  toJSON() {
    const obj = {};
    for (const [name, data] of this.cache) {
      obj[name] = { ...data };
    }
    return obj;
  }

  /**
   * Load cache from localStorage
   * @private
   */
  _loadFromStorage() {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (stored) {
        const data = JSON.parse(stored);
        for (const [name, cacheData] of Object.entries(data)) {
          this.cache.set(name, cacheData);
        }
      }
    } catch (e) {
      console.warn("EventIndexer: Failed to load from storage", e);
    }
  }

  /**
   * Save cache to localStorage
   * @private
   */
  _saveToStorage() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.toJSON()));
    } catch (e) {
      console.warn("EventIndexer: Failed to save to storage", e);
    }
  }
}

