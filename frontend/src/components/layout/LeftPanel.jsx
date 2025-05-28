import './LeftPanel.css'

const LeftPanel = () => {
  return (
    <div className="left-panel">
      <div className="panel-header">
        <h2>Trading Assistant</h2>
      </div>
      <div className="panel-content">
        <div className="menu-item">Dashboard</div>
        <div className="menu-item">Portfolio</div>
        <div className="menu-item">Markets</div>
        <div className="menu-item">Orders</div>
      </div>
    </div>
  )
}

export default LeftPanel 