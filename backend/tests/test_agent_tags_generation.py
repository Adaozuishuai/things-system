import sys
import os
import json
import asyncio
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agent.agents import RefinementAgent
from app.agent.orchestrator import extract_json_from_text, AgentOrchestrator

# Mock Model Response
class MockModelResponse:
    def __init__(self, content):
        self.text = content
        self.content = [{"type": "text", "text": content}]

# Mock Chat Model
class MockChatModel:
    def __init__(self, response_text):
        self.response_text = response_text
        
    async def __call__(self, messages):
        return MockModelResponse(self.response_text)

async def test_refinement_logic():
    print("=== Testing Refinement Agent Tag Generation Logic ===")
    
    # 1. Simulate LLM Output (Correct JSON)
    print("\n[Case 1] Valid JSON Output")
    valid_json_response = """
    {
        "title": "Refined Title",
        "summary": "Refined Summary",
        "tags": [
            {"label": "China", "color": "red"},
            {"label": "Economy", "color": "blue"}
        ]
    }
    """
    
    mock_model = MockChatModel(valid_json_response)
    agent = RefinementAgent(name="TestRefiner", model=mock_model)
    
    # Simulate input
    input_msg = "Raw Title\nRaw Summary\nOriginal Text"
    
    try:
        response_msg = await agent.reply(input_msg)
        print(f"Agent Raw Reply: {response_msg.content}")
        
        extracted = extract_json_from_text(response_msg.content)
        print(f"Extracted Data: {json.dumps(extracted, indent=2, ensure_ascii=False)}")
        
        if "tags" in extracted and len(extracted["tags"]) == 2:
            print("✅ Tags extracted successfully.")
        else:
            print("❌ Tags missing or incorrect.")
            
    except Exception as e:
        print(f"❌ Error in Case 1: {e}")

    # 2. Simulate LLM Output (Markdown Block)
    print("\n[Case 2] Markdown JSON Output")
    markdown_response = """
    Here is the analysis:
    ```json
    {
        "title": "Refined Title 2",
        "summary": "Refined Summary 2",
        "tags": [
            {"label": "USA", "color": "red"}
        ]
    }
    ```
    """
    
    mock_model_md = MockChatModel(markdown_response)
    agent_md = RefinementAgent(name="TestRefinerMD", model=mock_model_md)
    
    try:
        response_msg = await agent_md.reply(input_msg)
        extracted = extract_json_from_text(response_msg.content)
        print(f"Extracted Data: {json.dumps(extracted, indent=2, ensure_ascii=False)}")
        
        if "tags" in extracted and len(extracted["tags"]) == 1:
            print("✅ Tags extracted successfully from Markdown.")
        else:
            print("❌ Tags extraction failed for Markdown.")
            
    except Exception as e:
        print(f"❌ Error in Case 2: {e}")

    # 3. Simulate Integration in Orchestrator (Mocking Agent)
    print("\n[Case 3] Orchestrator Integration")
    orch = AgentOrchestrator()
    # Manually inject our mock agent
    orch.refinement_agent = agent
    orch.agentscope_inited = True # Bypass check
    
    raw_item = {
        "id": "123",
        "title": "Raw",
        "summary": "Raw",
        "original": "Raw"
    }
    
    refined_item = await orch.refine_intel_item(raw_item)
    print(f"Orchestrator Result Item: {json.dumps(refined_item, indent=2, ensure_ascii=False)}")
    
    if "tags" in refined_item and len(refined_item["tags"]) == 2:
         print("✅ Orchestrator successfully merged tags.")
    else:
         print("❌ Orchestrator failed to merge tags.")

if __name__ == "__main__":
    asyncio.run(test_refinement_logic())
