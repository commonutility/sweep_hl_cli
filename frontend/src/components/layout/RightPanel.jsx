import { useRef, useEffect, useState } from 'react'
import './RightPanel.css'
import { sendMessage } from '../../services/api'

const RightPanel = () => {
  const textareaRef = useRef(null)
  const textDisplayRef = useRef(null)
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleTextareaChange = (e) => {
    const textarea = e.target
    setInputValue(textarea.value)
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

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    if (textDisplayRef.current) {
      textDisplayRef.current.scrollTop = textDisplayRef.current.scrollHeight
    }
  }, [messages])

  const handleSendClick = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage = inputValue.trim()
    setInputValue('')
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    // Add user message to display
    setMessages(prev => [...prev, { type: 'user', content: userMessage }])
    setIsLoading(true)

    try {
      // Send message to backend
      const response = await sendMessage(userMessage)
      
      // Add assistant response to display
      setMessages(prev => [...prev, { 
        type: 'assistant', 
        content: response.response,
        toolCalls: response.tool_calls 
      }])
    } catch (error) {
      // Add error message
      setMessages(prev => [...prev, { 
        type: 'error', 
        content: 'Failed to send message. Please try again.' 
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendClick()
    }
  }

  return (
    <div className="right-panel">
      <div className="right-panel-content">
        <div className="text-display-area" ref={textDisplayRef}>
          {messages.length === 0 ? (
            <p className="placeholder-text">Start a conversation...</p>
          ) : (
            messages.map((message, index) => (
              <div key={index} className={`message message-${message.type}`}>
                <strong>{message.type === 'user' ? 'You: ' : message.type === 'assistant' ? 'Assistant: ' : 'Error: '}</strong>
                <span>{message.content}</span>
              </div>
            ))
          )}
          {isLoading && (
            <div className="message message-loading">
              <span>Assistant is thinking...</span>
            </div>
          )}
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
              value={inputValue}
              onChange={handleTextareaChange}
              onKeyPress={handleKeyPress}
              rows="1"
              disabled={isLoading}
            />
          </div>
          <div className="chatbox-section chatbox-bottom">
            <button 
              className="send-button"
              onClick={handleSendClick}
              disabled={isLoading || !inputValue.trim()}
            >
              {isLoading ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RightPanel 