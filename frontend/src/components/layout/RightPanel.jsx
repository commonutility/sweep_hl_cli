import './RightPanel.css'

const RightPanel = () => {
  return (
    <div className="right-panel">
      <div className="right-panel-content">
        {/* Right panel content will go here */}
      </div>
      <div className="right-panel-chatbox-container">
        <input 
          type="text" 
          className="right-panel-chatbox"
          placeholder="Type a message..."
        />
      </div>
    </div>
  )
}

export default RightPanel 