import React from 'react';
import './App.css'
import LeftPanel from './components/layout/LeftPanel'
import MainPanel from './components/layout/MainPanel'
import RightPanel from './components/layout/RightPanel'
import NetworkIndicator from './components/NetworkIndicator'

function App() {
  return (
    <div className="app">
      <div className="app-header">
        <NetworkIndicator />
      </div>
      <div className="app-content">
        <LeftPanel />
        <MainPanel />
        <RightPanel />
      </div>
    </div>
  )
}

export default App
