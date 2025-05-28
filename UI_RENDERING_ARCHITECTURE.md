# UI Rendering Architecture

## Overview

This document describes the UI rendering architecture that allows the LLM-powered chat assistant to dynamically render UI components in response to user queries.

## Architecture Components

### 1. Backend Components

#### Tools Definition (`src/reasoning/tools.py`)
- Defines UI rendering tools available to the LLM:
  - `render_asset_view`: Display asset price charts
  - `render_portfolio_view`: Show portfolio overview
  - `render_trade_form`: Open trading interface
  - `render_order_history`: Display trade history

#### LLM Client (`src/reasoning/llm_client.py`)
- Enhanced system prompt that explains UI rendering capabilities
- Provides examples to guide the LLM on when to use UI tools
- Uses GPT-4o model for better understanding

#### Response Manager (`src/reasoning/chat/response_manager.py`)
- Distinguishes between UI tools and data tools
- Formats UI actions for frontend consumption
- Generates user-friendly messages for UI actions

#### Tool Handler (`src/reasoning/chat/tool_handler.py`)
- Executes UI tool calls
- Generates UI action objects with:
  - `action`: The action type (e.g., "render_component")
  - `component`: Component name to render
  - `props`: Properties to pass to the component
  - `target`: Where to render (e.g., "main_panel")

### 2. Frontend Components

#### UI State Manager (`frontend/src/services/uiStateManager.js`)
- Manages UI state and action dispatching
- Subscribe/dispatch pattern for components
- Tracks active components and their state

#### Component Registry (`frontend/src/services/componentRegistry.js`)
- Dynamic component registration and retrieval
- Allows components to be loaded by name

#### Main Panel (`frontend/src/components/layout/MainPanel.jsx`)
- Subscribes to UI actions for the main panel
- Dynamically renders components based on actions
- Shows default view when no component is active

#### Chat Box (`frontend/src/components/chat/ChatBox.jsx`)
- Sends chat messages to backend
- Receives responses with UI actions
- Dispatches UI actions through the state manager

## Data Flow

1. **User Input**: User types a message in the chat (e.g., "Show me BTC chart")

2. **Backend Processing**:
   - LLM receives the message with enhanced context
   - LLM decides to call `render_asset_view` tool
   - Tool handler generates UI action object
   - Response includes both message and UI action

3. **Frontend Rendering**:
   - ChatBox receives response with UI action
   - Dispatches action through UIStateManager
   - MainPanel receives action and renders AssetPage
   - AssetPage fetches data and displays chart

## Example Interactions

### Viewing an Asset
```
User: "Show me Bitcoin"
LLM: [Calls render_asset_view(symbol="BTC")]
Response: "Displaying BTC chart..."
UI: Renders AssetPage component with BTC data
```

### Viewing Portfolio
```
User: "What are my positions?"
LLM: [Calls render_portfolio_view()]
Response: "Displaying your portfolio..."
UI: Renders PortfolioView component
```

## Adding New UI Components

1. **Define the tool** in `src/reasoning/tools.py`:
   ```python
   {
       "type": "function",
       "function": {
           "name": "render_new_component",
           "description": "Description for LLM",
           "parameters": {...}
       }
   }
   ```

2. **Add handler** in `src/reasoning/chat/tool_handler.py`:
   ```python
   def _handle_render_new_component(self, args):
       return {
           "action": "render_component",
           "component": "NewComponent",
           "props": {...},
           "target": "main_panel"
       }
   ```

3. **Create React component** in `frontend/src/components/`

4. **Register component** in MainPanel:
   ```javascript
   componentRegistry.register('NewComponent', NewComponent);
   ```

## Benefits

- **Natural Language UI**: Users can navigate the app using natural language
- **Context-Aware**: LLM understands context and chooses appropriate UI
- **Extensible**: Easy to add new components and interactions
- **Decoupled**: Frontend and backend communicate through well-defined actions 