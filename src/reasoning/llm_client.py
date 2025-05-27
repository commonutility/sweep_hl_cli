import os
import openai # Ensure the openai package is installed: pip install openai
import traceback
import json # For parsing arguments if/when we add tool calls back

# Import tool definitions
from .tools import get_database_query_tools # Assuming tools.py is in the same directory

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

        available_tools = get_database_query_tools() # Get current tool definitions
        # Later, we can extend this to include trading tools etc.
        # e.g., all_tools = get_database_query_tools() + get_trading_action_tools()

        messages = [
            {"role": "system", "content": "You are a helpful trading assistant that can interact with a local database of trades and positions. You have access to the conversation history and can reference previous messages. Based on the user's request, decide if a specific function (tool) should be called to answer the query. Only use the provided tools. If a tool is appropriate, specify the function name and any necessary arguments. If no tool is suitable or the user is just chatting, respond directly."}
        ]
        
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

        print(f"[LLMClient] Sending prompt to OpenAI model (gpt-4o) with {len(available_tools)} tools defined.")
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o", # Updated to use GPT-4o
                messages=messages,
                tools=available_tools,
                tool_choice="auto" # Let the model decide
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


if __name__ == '__main__':
    print("Testing LLMClient Class with Tool Calling...")
    llm_service = LLMClient()

    if llm_service.is_ready():
        print("\nLLMClient is ready.")
        
        prompts = [
            "Show me all my trades.",
            "What are my current positions?",
            "What's the weather like?", # Should be a direct text response
            "Buy 0.01 BTC" # No tool for this yet, should be direct text or different handling
        ]

        for p in prompts:
            print(f"\n--- Testing Prompt: '{p}' ---")
            action = llm_service.decide_action_with_llm(p)
            print(f"Action decided: {json.dumps(action, indent=2)}")
            # In a real app, you would now execute the tool call if action['type'] == 'tool_call'
            # and potentially send the result back to the LLM.
    else:
        print("\nLLMClient is NOT ready. Check API key and logs.") 