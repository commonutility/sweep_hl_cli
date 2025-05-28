import os
import openai # Ensure the openai package is installed: pip install openai
import traceback
import json # For parsing arguments if/when we add tool calls back

# Import tool definitions
from .tools import get_all_tools # Import all tools including UI tools

class LLMClient:
    """
    A client to interact with OpenAI's LLM APIs.
    Handles client initialization and provides methods for making API calls.
    """
    def __init__(self):
        """
        Initializes the OpenAI client using the API key from environment variables.
        """
        self.client = None
        self.initialized_successfully = False
        print("[LLMClient] Attempting to initialize OpenAI client...")
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print("[LLMClient] ERROR: OPENAI_API_KEY environment variable not found or is empty.")
            return
        else:
            print(f"[LLMClient] OPENAI_API_KEY found. Length: {len(api_key)}")
        
        try:
            print("[LLMClient] Attempting to create openai.OpenAI() instance...")
            self.client = openai.OpenAI(api_key=api_key)
            print("[LLMClient] openai.OpenAI() instance created successfully.")
            
            print("[LLMClient] Attempting test call (models.list())...")
            try:
                self.client.models.list() # A lightweight call
                print("[LLMClient] OpenAI client authentication test (models.list) successful.")
                self.initialized_successfully = True
            except openai.AuthenticationError as e_auth: 
                print(f"[LLMClient] OpenAI API Authentication Error during models.list test: {e_auth}. Check your API key.")
                self.client = None # Invalidate client
            except Exception as e_test:
                print(f"[LLMClient] OpenAI client test call (models.list) failed with non-auth error: {e_test}. API access unverified, but client object exists.")
                self.initialized_successfully = False 
            
            if self.initialized_successfully:
                print("[LLMClient] OpenAI client initialization complete and verified.")
            else:
                print("[LLMClient] OpenAI client instantiated but API access test (models.list) failed or had issues.")

        except openai.AuthenticationError as e_auth_init: 
            print(f"[LLMClient] ERROR: OpenAI API Authentication Error during client instantiation: {e_auth_init}. Check your API key.")
            self.client = None
        except Exception as e_init:
            print(f"[LLMClient] ERROR during openai.OpenAI() instantiation: {e_init}")
            self.client = None

    def is_ready(self) -> bool:
        """Checks if the client was initialized successfully and is ready to use."""
        return self.client is not None and self.initialized_successfully

    def decide_action_with_llm(self, user_prompt: str, conversation_history: list = None):
        """
        Sends a user prompt to the LLM, provides it with available tools,
        and returns either the LLM's direct text response or a tool call decision.
        
        Args:
            user_prompt: The current user message
            conversation_history: Optional list of previous messages in format
                                [{"role": "user/assistant", "content": "..."}]
        """
        print(f"\n[LLMClient] Received prompt for LLM action decision: '{user_prompt}'")
        if not self.is_ready():
            print("[LLMClient] OpenAI client not ready. Cannot process prompt.")
            return {"type": "error", "status": "error_openai_client_not_ready", "prompt": user_prompt}

        available_tools = get_all_tools() # Get current tool definitions
        
        # Enhanced system prompt that explains UI rendering capabilities
        system_prompt = """You are a helpful trading assistant for a Hyperliquid trading application. You have three main capabilities:

1. **Answer questions about trading, markets, and crypto**: You can respond to general queries and provide information about trading, markets, and the application.

2. **Query the database for trade history and positions**: You can access the local database to retrieve:
   - Trading history (get_all_trades_from_db)
   - Current positions (get_current_positions_from_db)

3. **Display UI components for charts, portfolio, and trading**: You can display interactive UI components in the main panel:
   - render_asset_view: Display price charts and asset information
   - render_portfolio_view: Show the user's portfolio overview
   - render_trade_form: Open a trading form
   - render_order_history: Display order/trade history

**CRITICAL RULES FOR UI RENDERING:**
- ALWAYS use render_asset_view when users mention ANY of these (regardless of how they phrase it):
  - Asset names (BTC, ETH, SOL, etc.)
  - Words like: price, chart, show, display, view
  - Questions about asset values or prices
  - Even simple mentions like "btc?" or "solana?"
  
- NEVER just say "Displaying X chart..." without actually calling the render_asset_view tool
- When in doubt about whether to show a chart, ALWAYS call render_asset_view
- For trading pairs like "BTC/ETH", use render_asset_view with symbol="BTC" and quote_asset="ETH"

**Examples that MUST trigger render_asset_view:**
- "btc" → render_asset_view(symbol="BTC")
- "solana?" → render_asset_view(symbol="SOL")
- "price of eth?" → render_asset_view(symbol="ETH")
- "show me bitcoin" → render_asset_view(symbol="BTC")
- "btc chart?" → render_asset_view(symbol="BTC")
- "what's ethereum?" → render_asset_view(symbol="ETH")
- "btc/eth" → render_asset_view(symbol="BTC", quote_asset="ETH")

Remember: Users expect to see charts when they mention assets. Always use the tools, don't just describe what you would do."""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if conversation_history:
            # Limit to last 20 messages to avoid token limits
            recent_history = conversation_history[-20:]
            for msg in recent_history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        # Add current user message
        messages.append({"role": "user", "content": user_prompt})
        
        print(f"[LLMClient] Sending prompt to OpenAI model (gpt-4o-mini) with {len(available_tools)} tools defined.")
        try:
            completion = self.client.chat.completions.create(
                model="o4-mini", # Updated to use GPT-o4-mini
                messages=messages,
                tools=available_tools,
                tool_choice="auto", 
                temperature = 1# Let the model decide
            )

            response_message = completion.choices[0].message

            if response_message.tool_calls:
                print("[LLMClient] LLM decided to call a tool.")
                tool_call = response_message.tool_calls[0] # For now, assume one tool call
                function_name = tool_call.function.name
                
                try:
                    arguments_json = tool_call.function.arguments
                    arguments = json.loads(arguments_json)
                except json.JSONDecodeError as e_json_args:
                    print(f"[LLMClient] ERROR: Could not parse JSON arguments for tool {function_name}: {arguments_json}. Error: {e_json_args}")
                    return {"type": "error", "status": "error_tool_argument_parsing", "function_name": function_name, "raw_arguments": arguments_json, "error_message": str(e_json_args)}

                print(f"[LLMClient] Tool call details: Function='{function_name}', Arguments='{arguments}'")
                return {
                    "type": "tool_call", 
                    "function_name": function_name, 
                    "arguments": arguments,
                    "tool_call_id": tool_call.id # Important for potential follow-up if tool execution result is sent back to LLM
                }
            elif response_message.content:
                response_text = response_message.content.strip()
                print(f"[LLMClient] Received direct text response from LLM: '{response_text[:200]}...'")
                return {"type": "text_response", "status": "success", "llm_response_text": response_text}
            else:
                print("[LLMClient] LLM response did not contain tool calls or content.")
                return {"type": "error", "status": "error_empty_llm_response"}

        except openai.AuthenticationError as e_auth:
            print(f"[LLMClient] OpenAI API Authentication Error during chat: {e_auth}. Check your API key.")
            return {"type": "error", "status": "error_authentication", "prompt": user_prompt, "error_message": str(e_auth)}
        except openai.APIConnectionError as e_conn:
            print(f"[LLMClient] OpenAI API Connection Error during chat: {e_conn}.")
            return {"type": "error", "status": "error_connection", "prompt": user_prompt, "error_message": str(e_conn)}
        except openai.RateLimitError as e_rate:
            print(f"[LLMClient] OpenAI API Rate Limit Error during chat: {e_rate}.")
            return {"type": "error", "status": "error_rate_limit", "prompt": user_prompt, "error_message": str(e_rate)}
        except Exception as e:
            print(f"[LLMClient] An unexpected error occurred during chat completion with tools: {e}")
            traceback.print_exc()
            return {"type": "error", "status": "error_unknown_chat_completion", "prompt": user_prompt, "error_message": str(e)}

