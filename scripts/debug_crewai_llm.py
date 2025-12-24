
import os
from crewai import LLM, Agent

def test_crewai_llm():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    if not api_key:
        print("Skipping test: No API Key")
        return

    print(f"Testing crewai.LLM with model={model}, base_url={api_base}")
    
    try:
        # Construct LLM using CrewAI's native class
        # Note: LiteLLM usually expects 'openai/' prefix for compatible endpoints if the model name isn't standard openai
        # But let's try passing parameters explicitly.
        
        my_llm = LLM(
            model=model, # or f"openai/{model}"
            api_key=api_key,
            base_url=api_base
        )
        
        print("LLM initialized. Creating agent...")
        agent = Agent(
            role="Test Agent",
            goal="Say hello",
            backstory="I am a test.",
            llm=my_llm
        )
        
        print("Agent created. Invoking...")
        # We can't easily invoke agent without a task, but we can try to call the LLM directly via agent?
        # Or just call llm.call()
        response = my_llm.call([{"role": "user", "content": "Hello"}])
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_crewai_llm()
