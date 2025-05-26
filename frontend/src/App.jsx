import './App.css'
import LeftPanel from './components/layout/LeftPanel'
import MainPanel from './components/layout/MainPanel'
import RightPanel from './components/layout/RightPanel'
import ChatBox from './components/chat/ChatBox'

function App() {
  return (
    <div className="app-container">
      <LeftPanel />
      <MainPanel>
        {/* Example: ChatBox component rendered inside MainPanel */}
        <ChatBox />
      </MainPanel>
      <RightPanel />
    </div>
  )
}

export default App
