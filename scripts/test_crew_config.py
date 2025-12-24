
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from intelligent_meal_planner.agents.crew import MealPlanningCrew

def test_crew_config():
    # Mock environment variables
    os.environ["DEEPSEEK_API_KEY"] = "sk-test-key"
    os.environ["DEEPSEEK_API_BASE"] = "https://api.deepseek.com/v1"
    os.environ["DEEPSEEK_MODEL"] = "deepseek-chat"
    os.environ["OPENAI_API_KEY"] = "sk-test-key" # Satisfy CrewAI/LangChain validation
    
    try:
        crew = MealPlanningCrew()
        
        print("Crew initialized.")
        if crew.llm:
            print(f"LLM configured: {type(crew.llm).__name__}")
            # Try to get base URL from different possible attributes
            base_url = getattr(crew.llm, "openai_api_base", None) or getattr(crew.llm, "base_url", None)
            print(f"Base URL: {base_url}")
            print(f"Model: {crew.llm.model_name}")
            
            if base_url == "https://api.deepseek.com/v1" and crew.llm.model_name == "deepseek-chat":
                print("SUCCESS: DeepSeek configuration correctly loaded.")
            else:
                print("FAILURE: Configuration mismatch.")
        else:
            print("FAILURE: LLM is None.")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_crew_config()
