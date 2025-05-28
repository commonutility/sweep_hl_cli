class WebSocketService {
  constructor() {
    this.ws = null
    this.subscriptions = new Map()
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 1000
    this.isConnecting = false
    this.messageQueue = []
    this.nextSubscriptionId = 1
  }

  connect(url = 'wss://api.hyperliquid.xyz/ws') {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('[WebSocketService] Already connected')
      return Promise.resolve()
    }

    if (this.isConnecting) {
      console.log('[WebSocketService] Connection already in progress')
      return new Promise((resolve) => {
        const checkConnection = setInterval(() => {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            clearInterval(checkConnection)
            resolve()
          }
        }, 100)
      })
    }

    this.isConnecting = true

    return new Promise((resolve, reject) => {
      try {
        console.log('[WebSocketService] Connecting to', url)
        this.ws = new WebSocket(url)

        this.ws.onopen = () => {
          console.log('[WebSocketService] Connected')
          this.isConnecting = false
          this.reconnectAttempts = 0
          
          // Process queued messages
          while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift()
            this.send(message)
          }
          
          // Resubscribe to all active subscriptions
          this.subscriptions.forEach((subscription, id) => {
            if (subscription.active) {
              this.send(subscription.message)
            }
          })
          
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleMessage(data)
          } catch (error) {
            console.error('[WebSocketService] Error parsing message:', error)
          }
        }

        this.ws.onerror = (error) => {
          console.error('[WebSocketService] WebSocket error:', error)
          this.isConnecting = false
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('[WebSocketService] Connection closed')
          this.isConnecting = false
          this.handleReconnect()
        }
      } catch (error) {
        console.error('[WebSocketService] Error creating WebSocket:', error)
        this.isConnecting = false
        reject(error)
      }
    })
  }

  handleMessage(data) {
    // Handle subscription response
    if (data.channel === 'subscriptionResponse') {
      console.log('[WebSocketService] Subscription confirmed:', data.data)
      return
    }

    // Handle data updates
    if (data.channel && data.data) {
      this.subscriptions.forEach((subscription) => {
        if (subscription.channel === data.channel && subscription.callback) {
          subscription.callback(data.data)
        }
      })
    }
  }

  subscribe(channel, subscriptionData, callback) {
    const id = this.nextSubscriptionId++
    const message = {
      method: 'subscribe',
      subscription: subscriptionData
    }

    const subscription = {
      id,
      channel,
      message,
      callback,
      active: true
    }

    this.subscriptions.set(id, subscription)

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.send(message)
    } else {
      this.messageQueue.push(message)
    }

    return id
  }

  unsubscribe(subscriptionId) {
    const subscription = this.subscriptions.get(subscriptionId)
    if (!subscription) return

    subscription.active = false
    
    const unsubscribeMessage = {
      method: 'unsubscribe',
      subscription: subscription.message.subscription
    }

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.send(unsubscribeMessage)
    }

    this.subscriptions.delete(subscriptionId)
  }

  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      this.messageQueue.push(message)
    }
  }

  handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocketService] Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    
    console.log(`[WebSocketService] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)
    
    setTimeout(() => {
      this.connect().catch(error => {
        console.error('[WebSocketService] Reconnection failed:', error)
      })
    }, delay)
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.subscriptions.clear()
    this.messageQueue = []
    this.reconnectAttempts = 0
  }
}

// Create singleton instance
const wsService = new WebSocketService()

export default wsService 