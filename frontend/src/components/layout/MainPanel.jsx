import React, { useState, useEffect } from 'react';
import './MainPanel.css'
import AssetPage from '../main_panel/assets/AssetPage';
import PortfolioView from '../main_panel/portfolio/PortfolioView';
import OrderHistory from '../main_panel/history/OrderHistory';
import MultiPanelAsset from '../assets/MultiPanelAsset';
import { uiStateManager } from '../../services/uiStateManager';
import { componentRegistry } from '../../services/componentRegistry';
import { UI_TARGETS } from '../../constants/uiActions';

// Register components that can be dynamically loaded
// This allows the UI state manager to render components by name
console.log('[MainPanel] About to register components');
console.log('[MainPanel] AssetPage component:', AssetPage);
console.log('[MainPanel] PortfolioView component:', PortfolioView);
console.log('[MainPanel] OrderHistory component:', OrderHistory);
console.log('[MainPanel] MultiPanelAsset component:', MultiPanelAsset);

componentRegistry.register('AssetPage', AssetPage);
componentRegistry.register('PortfolioView', PortfolioView);
componentRegistry.register('OrderHistory', OrderHistory);
componentRegistry.register('MultiPanelAsset', MultiPanelAsset);

// TODO: Create and register these components when they're implemented
// componentRegistry.register('TradeForm', TradeForm);

console.log('[MainPanel] Components registered:', componentRegistry.getRegisteredNames());

const MainPanel = () => {
  const [activeComponent, setActiveComponent] = useState(null);
  const [componentProps, setComponentProps] = useState({});

  useEffect(() => {
    console.log('[MainPanel] Mounting MainPanel component');
    
    // Subscribe to UI actions for the main panel
    console.log('[MainPanel] Subscribing to UI_TARGETS.MAIN_PANEL:', UI_TARGETS.MAIN_PANEL);
    
    const unsubscribe = uiStateManager.subscribe(UI_TARGETS.MAIN_PANEL, (action) => {
      console.log('[MainPanel] Received UI action:', action);
      console.log('[MainPanel] Action type:', action.action);
      console.log('[MainPanel] Component to render:', action.component);
      
      if (action.action === 'render_component') {
        console.log('[MainPanel] Processing render_component action');
        const Component = componentRegistry.get(action.component);
        console.log('[MainPanel] Retrieved component from registry:', Component);
        
        if (Component) {
          console.log('[MainPanel] Setting active component:', action.component);
          console.log('[MainPanel] Setting component props:', action.props);
          setActiveComponent(() => Component);
          setComponentProps(action.props || {});
        } else {
          console.warn(`[MainPanel] Component not found: ${action.component}`);
        }
      } else if (action.action === 'close_component') {
        console.log('[MainPanel] Closing component');
        setActiveComponent(null);
        setComponentProps({});
      }
    });

    console.log('[MainPanel] Subscription complete');
    
    // Test the subscription immediately
    setTimeout(() => {
      console.log('[MainPanel] Testing subscription with a dummy action');
      const testAction = {
        action: 'test',
        target: 'main_panel'
      };
      uiStateManager.dispatch(testAction);
    }, 100);

    // Cleanup on unmount
    return () => {
      console.log('[MainPanel] Unmounting MainPanel, unsubscribing');
      unsubscribe();
    };
  }, []);

  // Log when activeComponent changes
  useEffect(() => {
    console.log('[MainPanel] activeComponent changed:', activeComponent);
    console.log('[MainPanel] componentProps:', componentProps);
  }, [activeComponent, componentProps]);

  // Default view when no component is active
  const renderDefaultView = () => (
    <div className="main-panel-default">
      <h2>Welcome to Hyperliquid Trading</h2>
      <p>Use the chat to interact with your trading assistant.</p>
      <div className="quick-actions">
        <h3>Try asking:</h3>
        <ul>
          <li>"Show me BTC price chart"</li>
          <li>"What are my current positions?"</li>
          <li>"Show my portfolio"</li>
          <li>"Display my trade history"</li>
        </ul>
      </div>
    </div>
  );

  console.log('[MainPanel] Rendering, activeComponent:', activeComponent);

  return (
    <div className="main-panel">
      {activeComponent ? (
        React.createElement(activeComponent, componentProps)
      ) : (
        renderDefaultView()
      )}
    </div>
  )
}

export default MainPanel 