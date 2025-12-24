
import os
import sys
from langchain_openai import ChatOpenAI

def test_connection():
    # Load from .env manually or just use what's in the environment if already loaded
    # For independent testing, let's try to simulate what happens in the app
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    print(f"DEBUG: Using settings -> Base: {api_base}, Model: {model}")
    
    if not api_key:
        print("ERROR: DEEPSEEK_API_KEY not found in env.")
        return

    # Set OpenAI env vars as we did in the code
    # os.environ["OPENAI_API_KEY"] = api_key
    # os.environ["OPENAI_API_BASE"] = api_base
    
    print("DEBUG: Initializing ChatOpenAI...")
    try:
        # Try usage 1: base_url
        llm = ChatOpenAI(
            model=model,
            base_url=api_base,
            api_key=api_key,
            temperature=0.7
        )
        
        print(f"DEBUG: Inspecting LLM object: base_url={getattr(llm, 'base_url', 'N/A')}, openai_api_base={getattr(llm, 'openai_api_base', 'N/A')}")
        
        print("DEBUG: Attempting to invoke...")
        response = llm.invoke("Hello, are you DeepSeek?")
        print(f"SUCCESS: Response received: {response.content}")
        
    except Exception as e:
        print(f"FAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_connection()
