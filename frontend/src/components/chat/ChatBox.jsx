import React, { useState, useRef, useEffect } from 'react';
import './ChatBox.css'
import { uiStateManager } from '../../services/uiStateManager';

const ChatBox = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [inputValue]);

  // Load session from localStorage on mount
  useEffect(() => {
    const savedSessionId = localStorage.getItem('chatSessionId');
    if (savedSessionId) {
      setSessionId(savedSessionId);
    }
  }, []);

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    
    // Add user message to chat
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();
      console.log('[ChatBox] Full response from backend:', data);
      
      // Update session ID if new
      if (data.session_id && data.session_id !== sessionId) {
        setSessionId(data.session_id);
        localStorage.setItem('chatSessionId', data.session_id);
      }

      // Add assistant message
      setMessages(prev => [...prev, { 
        type: 'assistant', 
        content: data.response,
        responseType: data.type
      }]);

      // Handle UI actions if present
      if (data.ui_actions && data.ui_actions.length > 0) {
        console.log('[ChatBox] UI actions found:', data.ui_actions);
        console.log('[ChatBox] Number of UI actions:', data.ui_actions.length);
        
        data.ui_actions.forEach((action, index) => {
          console.log(`[ChatBox] Dispatching UI action ${index}:`, action);
          // Dispatch UI action through the state manager
          uiStateManager.dispatch(action);
        });
      } else {
        console.log('[ChatBox] No UI actions in response');
      }

      // Handle tool results if present (for display purposes)
      if (data.tool_results && data.tool_results.length > 0) {
        console.log('[ChatBox] Tool results:', data.tool_results);
        // Tool results are already formatted in the message
        // This is here for potential future enhancements
      }

    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, { 
        type: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.',
        isError: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewConversation = () => {
    setMessages([]);
    setSessionId(null);
    localStorage.removeItem('chatSessionId');
    setInputValue('');
  };

  return (
    <div className="chat-box">
      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.type} ${msg.isError ? 'error' : ''}`}>
            <div className="message-content">
              {msg.content}
              {msg.responseType === 'ui_action' && (
                <span className="ui-action-indicator"> ✨</span>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message assistant loading">
            <div className="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="chat-input-container">
        <textarea
          ref={textareaRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          className="chat-input"
          rows="1"
        />
        <div className="chat-buttons">
          <button 
            onClick={handleSend} 
            disabled={!inputValue.trim() || isLoading}
            className="send-button"
          >
            Send
          </button>
          <button 
            onClick={handleNewConversation}
            className="new-conversation-button"
          >
            New Conversation
          </button>
        </div>
      </div>
    </div>
  )
}

export default ChatBox 