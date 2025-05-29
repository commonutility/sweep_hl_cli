import React, { useState, useEffect } from 'react';
import './NetworkIndicator.css';

const NetworkIndicator = () => {
  const [network, setNetwork] = useState('testnet');
  const [isLoading, setIsLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    // Fetch current network on mount
    fetchNetwork();
  }, []);

  const fetchNetwork = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/network');
      const data = await response.json();
      setNetwork(data.network);
    } catch (error) {
      console.error('Failed to fetch network:', error);
    }
  };

  const switchNetwork = async (newNetwork) => {
    if (newNetwork === network) {
      setShowDropdown(false);
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/network', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newNetwork),
      });

      if (response.ok) {
        const data = await response.json();
        setNetwork(data.network);
        setShowDropdown(false);
        
        // Reload the page to ensure all components use the new network
        window.location.reload();
      } else {
        console.error('Failed to switch network');
      }
    } catch (error) {
      console.error('Error switching network:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="network-indicator">
      <button 
        className={`network-button ${network}`}
        onClick={() => setShowDropdown(!showDropdown)}
        disabled={isLoading}
      >
        <span className="network-dot"></span>
        <span className="network-text">
          {isLoading ? 'Switching...' : network.toUpperCase()}
        </span>
        <span className="network-arrow">▼</span>
      </button>
      
      {showDropdown && !isLoading && (
        <div className="network-dropdown">
          <button 
            className={`network-option ${network === 'testnet' ? 'active' : ''}`}
            onClick={() => switchNetwork('testnet')}
          >
            <span className="network-dot testnet"></span>
            TESTNET
          </button>
          <button 
            className={`network-option ${network === 'mainnet' ? 'active' : ''}`}
            onClick={() => switchNetwork('mainnet')}
          >
            <span className="network-dot mainnet"></span>
            MAINNET
          </button>
        </div>
      )}
    </div>
  );
};

export default NetworkIndicator; 