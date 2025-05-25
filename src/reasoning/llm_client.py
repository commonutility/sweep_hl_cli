import os
import openai # Ensure the openai package is installed: pip install openai
import traceback
import json # For parsing arguments if/when we add tool calls back

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

    def get_llm_chat_response(self, user_prompt: str):
        """
        Sends a user prompt to the LLM for a direct chat response (no tools yet).
        """
        print(f"\n[LLMClient] Received prompt for direct chat: '{user_prompt}'")
        if not self.is_ready():
            print("[LLMClient] OpenAI client not ready or not initialized. Cannot send prompt.")
            return {"status": "error_openai_client_not_ready", "prompt": user_prompt}

        print(f"[LLMClient] Sending prompt to OpenAI model (gpt-3.5-turbo)...")
        try:
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_prompt}
                ]
            )
            response_content = completion.choices[0].message.content
            print(f"[LLMClient] Received LLM response: '{response_content[:200]}...'") # Print a snippet
            return {
                "status": "success", 
                "prompt": user_prompt,
                "llm_response_text": response_content
            }
        except openai.AuthenticationError as e_auth:
            print(f"[LLMClient] OpenAI API Authentication Error during chat: {e_auth}. Check your API key.")
            return {"status": "error_authentication", "prompt": user_prompt, "error_message": str(e_auth)}
        except openai.APIConnectionError as e_conn:
            print(f"[LLMClient] OpenAI API Connection Error during chat: {e_conn}.")
            return {"status": "error_connection", "prompt": user_prompt, "error_message": str(e_conn)}
        except openai.RateLimitError as e_rate:
            print(f"[LLMClient] OpenAI API Rate Limit Error during chat: {e_rate}.")
            return {"status": "error_rate_limit", "prompt": user_prompt, "error_message": str(e_rate)}
        except Exception as e:
            print(f"[LLMClient] An unexpected error occurred during chat completion: {e}")
            traceback.print_exc()
            return {"status": "error_unknown", "prompt": user_prompt, "error_message": str(e)}

# Example of how it might be used (for testing this file directly):
if __name__ == '__main__':
    print("Testing LLMClient Class...")
    # Ensure OPENAI_API_KEY is set in your environment to test initialization
    llm_service = LLMClient()

    if llm_service.is_ready():
        print("\nLLMClient is ready. Testing direct chat response:")
        test_prompt = "What is the main purpose of the Hyperliquid protocol?"
        response = llm_service.get_llm_chat_response(test_prompt)
        print(f"\nResponse for prompt '{test_prompt}':")
        if response and response.get("status") == "success":
            print(f"  LLM: {response.get('llm_response_text')}")
        else:
            print(f"  Error: {response}")
        
        test_prompt_2 = "Explain blockchain technology in simple terms."
        response_2 = llm_service.get_llm_chat_response(test_prompt_2)
        print(f"\nResponse for prompt '{test_prompt_2}':")
        if response_2 and response_2.get("status") == "success":
            print(f"  LLM: {response_2.get('llm_response_text')}")
        else:
            print(f"  Error: {response_2}")
    else:
        print("\nLLMClient is NOT ready. Check API key and logs.") 