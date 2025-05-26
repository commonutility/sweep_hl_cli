import { useRef, useEffect } from 'react'
import './RightPanel.css'

const RightPanel = () => {
  const textareaRef = useRef(null)

  const handleTextareaChange = (e) => {
    const textarea = e.target
    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto'
    // Set the height to match the content
    textarea.style.height = `${textarea.scrollHeight}px`
  }

  useEffect(() => {
    // Set initial height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [])

  const handleSendClick = () => {
    // Send functionality will be implemented later
    console.log('Send button clicked')
  }

  return (
    <div className="right-panel">
      <div className="right-panel-content">
        {/* Right panel content will go here */}
      </div>
      <div className="right-panel-chatbox-container">
        <div className="chatbox-wrapper">
          <div className="chatbox-section chatbox-top">
            {/* Top third - empty space for future components */}
          </div>
          <div className="chatbox-section chatbox-middle">
            <textarea 
              ref={textareaRef}
              className="right-panel-textarea"
              placeholder="Type a message..."
              onChange={handleTextareaChange}
              rows="1"
            />
          </div>
          <div className="chatbox-section chatbox-bottom">
            <button 
              className="send-button"
              onClick={handleSendClick}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RightPanel 