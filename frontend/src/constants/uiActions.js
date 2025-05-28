/**
 * UI Action Types for managing UI state changes from chat interactions
 */

export const UI_ACTIONS = {
  // Component rendering actions
  RENDER_COMPONENT: 'render_component',
  UPDATE_COMPONENT: 'update_component',
  CLOSE_COMPONENT: 'close_component',
  
  // Modal actions
  OPEN_MODAL: 'open_modal',
  CLOSE_MODAL: 'close_modal',
  
  // Notification actions
  SHOW_NOTIFICATION: 'show_notification',
  HIDE_NOTIFICATION: 'hide_notification',
  
  // Panel actions
  SWITCH_PANEL: 'switch_panel',
  SPLIT_PANEL: 'split_panel',
  
  // Navigation actions
  NAVIGATE_TO: 'navigate_to'
};

// Component names that can be rendered
export const UI_COMPONENTS = {
  ASSET_PAGE: 'AssetPage',
  PORTFOLIO_VIEW: 'PortfolioView',
  TRADE_FORM: 'TradeForm',
  ORDER_HISTORY: 'OrderHistory',
  MARKET_OVERVIEW: 'MarketOverview'
};

// Target panels where components can be rendered
export const UI_TARGETS = {
  MAIN_PANEL: 'main_panel',
  LEFT_PANEL: 'left_panel',
  RIGHT_PANEL: 'right_panel',
  MODAL: 'modal'
}; 