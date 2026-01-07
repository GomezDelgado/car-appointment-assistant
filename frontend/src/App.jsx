import { useState, useRef, useEffect } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/graphql'
const STORAGE_KEY = 'car-assistant-history'
const SESSION_KEY = 'car-assistant-session'
const MAX_HISTORY = 4

const DEFAULT_ACTIONS = [
  { label: 'Dealerships in Manhattan', message: 'Show me dealerships in Manhattan' },
  { label: 'Dealerships in Brooklyn', message: 'Show me dealerships in Brooklyn' },
]

function getSessionId() {
  let sessionId = sessionStorage.getItem(SESSION_KEY)
  if (!sessionId) {
    sessionId = 'session_' + Math.random().toString(36).substring(2, 15)
    sessionStorage.setItem(SESSION_KEY, sessionId)
  }
  return sessionId
}

function getStoredHistory() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

function renderText(text) {
  // Simple markdown bold parser: **text** -> <strong>text</strong>
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>
    }
    return part
  })
}

function saveToHistory(message) {
  const history = getStoredHistory()
  // Avoid duplicates
  const filtered = history.filter(h => h.message !== message)
  // Create short label from message
  const label = message.length > 30 ? message.substring(0, 30) + '...' : message
  const newHistory = [{ label, message }, ...filtered].slice(0, MAX_HISTORY)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(newHistory))
  return newHistory
}

function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m your Car Appointment Assistant. I can help you find dealerships, check availability, and book appointments. How can I help you today?'
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [quickActions, setQuickActions] = useState(() => {
    const history = getStoredHistory()
    return history.length > 0 ? history : DEFAULT_ACTIONS
  })
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (messageText) => {
    const userMessage = messageText || input.trim()
    if (!userMessage || loading) return

    // Save to history and update quick actions
    const newHistory = saveToHistory(userMessage)
    setQuickActions(newHistory)

    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setInput('')
    setLoading(true)

    try {
      const sessionId = getSessionId()
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: `mutation { chat(message: "${userMessage.replace(/"/g, '\\"')}", sessionId: "${sessionId}") { message success } }`
        })
      })

      const data = await response.json()

      if (data.data?.chat?.message) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.data.chat.message
        }])
      } else {
        throw new Error('Invalid response')
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, there was an error connecting to the server. Please try again.',
        error: true
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    sendMessage()
  }

  const handleQuickAction = (message) => {
    setInput(message)
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <span className="logo-icon">🚗</span>
          <h1>Car Appointment Assistant</h1>
        </div>
      </header>

      <div className="quick-actions">
        {quickActions.map((action, idx) => (
          <button
            key={idx}
            className="quick-action-btn"
            onClick={() => handleQuickAction(action.message)}
            disabled={loading}
            title={action.message}
          >
            {action.label}
          </button>
        ))}
      </div>

      <main className="chat-container">
        <div className="messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role} ${msg.error ? 'error' : ''}`}>
              <div className="message-content">
                {msg.content.split('\n').map((line, i) => (
                  <p key={i}>{renderText(line)}</p>
                ))}
              </div>
            </div>
          ))}
          {loading && (
            <div className="message assistant">
              <div className="message-content loading">
                <span className="dot"></span>
                <span className="dot"></span>
                <span className="dot"></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      <footer className="input-container">
        <form onSubmit={handleSubmit} className="input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={loading}
            autoFocus
          />
          <button type="submit" disabled={loading || !input.trim()}>
            Send
          </button>
        </form>
      </footer>
    </div>
  )
}

export default App
