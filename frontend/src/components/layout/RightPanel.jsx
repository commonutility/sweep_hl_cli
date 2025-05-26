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
        <div className="text-display-area">
          {/* This area can contain any mix of components */}
          <p>Sample text line 1</p>
          <p>Sample text line 2</p>
          <p>Sample text line 3</p>
          <p>This is a longer sample text to demonstrate how the text wraps and scrolls in the display area</p>
          
          {/* Example of a custom component */}
          <div className="custom-info-box">
            <strong>System Message:</strong> This is a custom component example
          </div>
          
          <p>More text here...</p>
          <p>And even more text...</p>
          <p>Keep scrolling to see more content</p>
          <p>The text display area is scrollable</p>
          <p>You can add as much content as needed</p>
          <p>It will scroll vertically when content overflows</p>
          
          {/* Another custom component example */}
          <div className="status-indicator">
            <span className="status-dot"></span>
            <span>Status: Active</span>
          </div>
          
          <p>Additional text content to test scrolling...</p>
          <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
          <p>Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
          <p>Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.</p>
          <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum.</p>
          <p>Excepteur sint occaecat cupidatat non proident, sunt in culpa qui.</p>
          <p>This demonstrates how the scrollbar appears when content overflows.</p>
          <p>You can continue adding more content as needed.</p>
          <p>The container will handle any type of React component.</p>
          <p>Mix and match text, custom components, images, etc.</p>
          <p>Everything will be scrollable within this container.</p>
          <p>The green background provides a nice contrast.</p>
          <p>Keep scrolling to see even more content below...</p>
          <p>Almost at the end of the sample content.</p>
          <p>This is the last line of sample text.</p>
        </div>
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