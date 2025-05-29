import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import PortfolioView from './components/main_panel/portfolio/PortfolioView'
import OrderHistory from './components/main_panel/history/OrderHistory'
import MainPanel from './components/layout/MainPanel'
import AssetPage from './components/main_panel/assets/AssetPage'
import MultiPanelAsset from './components/assets/MultiPanelAsset'
import ChatBox from './components/chat/ChatBox'
import NetworkIndicator from './components/NetworkIndicator'
import { uiStateManager } from './services/uiStateManager'
import './App.css'

function App() {
  useEffect(() => {
    // Set initial UI state
    uiStateManager.dispatch({
      action: 'render_component',
      component: 'PortfolioView',
      props: {},
      target: 'main_panel'
    })
  }, [])

  return (
    <Router>
      <div className="app">
        <NetworkIndicator />
        <div className="app-content">
          <div className="main-panel">
            <MainPanel />
          </div>
          <div className="chat-panel">
            <ChatBox />
          </div>
        </div>
      </div>
    </Router>
  )
}

export default App
