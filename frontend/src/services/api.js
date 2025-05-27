const API_URL = 'http://localhost:8000/api';

export const sendMessage = async (message, sessionId = null) => {
  try {
    const response = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        message,
        session_id: sessionId 
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};

export const getPriceHistory = async (symbol, days = 180) => {
  try {
    const response = await fetch(`${API_URL}/assets/${symbol}/price-history?days=${days}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching price history:', error);
    throw error;
  }
};

export const getCurrentPrice = async (symbol) => {
  try {
    const response = await fetch(`${API_URL}/assets/${symbol}/current`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching current price:', error);
    throw error;
  }
}; 