/**
 * UI State Manager for handling UI actions from chat interactions
 * This manages the communication between chat responses and UI components
 */

import { UI_ACTIONS } from '../constants/uiActions';

class UIStateManager {
  constructor() {
    // Map of target -> Set of listener callbacks
    this.listeners = new Map();
    
    // Current UI state
    this.state = {
      activeComponents: new Map(), // target -> component info
      modals: [],
      notifications: []
    };
  }

  /**
   * Subscribe to UI actions for a specific target
   * @param {string} target - The target to listen to (e.g., 'main_panel')
   * @param {Function} callback - The callback to invoke on UI actions
   * @returns {Function} Unsubscribe function
   */
  subscribe(target, callback) {
    if (!this.listeners.has(target)) {
      this.listeners.set(target, new Set());
    }
    
    this.listeners.get(target).add(callback);
    console.log(`[UIStateManager] Subscribed to target: ${target}`);
    console.log(`[UIStateManager] Total listeners for ${target}: ${this.listeners.get(target).size}`);
    
    // Return unsubscribe function
    return () => {
      const targetListeners = this.listeners.get(target);
      if (targetListeners) {
        targetListeners.delete(callback);
        console.log(`[UIStateManager] Unsubscribed from target: ${target}`);
      }
    };
  }

  /**
   * Dispatch a UI action
   * @param {Object} action - The UI action to dispatch
   */
  dispatch(action) {
    console.log('[UIStateManager] Dispatching action:', action);
    console.log('[UIStateManager] Action target:', action.target);
    console.log('[UIStateManager] Action type:', action.action);
    
    const { target, action: actionType } = action;
    
    // Update internal state based on action type
    switch (actionType) {
      case 'render_component':
        this.state.activeComponents.set(target, {
          component: action.component,
          props: action.props,
          timestamp: Date.now()
        });
        break;
        
      case 'close_component':
        this.state.activeComponents.delete(target);
        break;
        
      case 'open_modal':
        this.state.modals.push({
          id: action.modalId || Date.now(),
          component: action.component,
          props: action.props
        });
        break;
        
      case 'close_modal':
        this.state.modals = this.state.modals.filter(
          modal => modal.id !== action.modalId
        );
        break;
        
      case 'show_notification':
        this.state.notifications.push({
          id: action.notificationId || Date.now(),
          message: action.message,
          type: action.notificationType || 'info',
          duration: action.duration || 5000
        });
        break;
    }
    
    // Debug: Show all current listeners
    console.log('[UIStateManager] Current listeners map:', Array.from(this.listeners.keys()));
    
    // Notify listeners for the target
    if (target && this.listeners.has(target)) {
      const targetListeners = this.listeners.get(target);
      console.log(`[UIStateManager] Found ${targetListeners.size} listeners for target: ${target}`);
      
      targetListeners.forEach(callback => {
        try {
          console.log(`[UIStateManager] Calling listener for target: ${target}`);
          callback(action);
        } catch (error) {
          console.error('[UIStateManager] Error in listener callback:', error);
        }
      });
    } else {
      console.log(`[UIStateManager] No listeners found for target: ${target}`);
    }
    
    // Also notify global listeners (listening to '*')
    if (this.listeners.has('*')) {
      this.listeners.get('*').forEach(callback => {
        try {
          callback(action);
        } catch (error) {
          console.error('[UIStateManager] Error in global listener callback:', error);
        }
      });
    }
  }

  /**
   * Get the current state for a target
   * @param {string} target - The target to get state for
   * @returns {Object|null} The current state for the target
   */
  getState(target) {
    return this.state.activeComponents.get(target) || null;
  }

  /**
   * Get all active components
   * @returns {Map} Map of all active components
   */
  getAllActiveComponents() {
    return new Map(this.state.activeComponents);
  }

  /**
   * Clear all UI state
   */
  clearAll() {
    this.state.activeComponents.clear();
    this.state.modals = [];
    this.state.notifications = [];
    
    // Notify all listeners about the clear
    this.dispatch({
      action: 'CLEAR_ALL',
      target: '*'
    });
  }
}

// Create and export a singleton instance
export const uiStateManager = new UIStateManager(); 