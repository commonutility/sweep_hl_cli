import React from 'react';
import './App.css'
import LeftPanel from './components/layout/LeftPanel'
import MainPanel from './components/layout/MainPanel'
import RightPanel from './components/layout/RightPanel'

function App() {
  return (
    <div className="app">
      <LeftPanel />
      <MainPanel />
      <RightPanel />
      </div>
  )
}

export default App
