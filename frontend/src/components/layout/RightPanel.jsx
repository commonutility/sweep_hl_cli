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

  return (
    <div className="right-panel">
      <div className="right-panel-content">
        {/* Right panel content will go here */}
      </div>
      <div className="right-panel-chatbox-container">
        <textarea 
          ref={textareaRef}
          className="right-panel-chatbox"
          placeholder="Type a message..."
          onChange={handleTextareaChange}
          rows="1"
        />
      </div>
    </div>
  )
}

export default RightPanel 