import './App.css'
import LeftPanel from './components/layout/LeftPanel'
import MainPanel from './components/layout/MainPanel'
import RightPanel from './components/layout/RightPanel'
import AssetPage from './components/assets/AssetPage'

function App() {
  return (
    <div className="app-container">
      <LeftPanel />
      <MainPanel>
        {/* Display AssetPage for now - later this will be dynamic */}
        <AssetPage symbol="BTC" />
      </MainPanel>
      <RightPanel />
    </div>
  )
}

export default App
