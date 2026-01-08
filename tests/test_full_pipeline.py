import os
import sys
import asyncio
import json
from unittest.mock import MagicMock

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.agent.orchestrator import AgentOrchestrator
from app.services.payload_poller import PayloadPoller
from app.agent import agents

# Mock data based on data.json
MOCK_DOC = {
    "id": 18415,
    "no": None,
    "title": "黄仁勋：中国对辉达AI芯片需求“相当高”",
    "thingId": "01KEBGV4J6VP48CQ55GQVYHPS6",
    "publishDate": "2026-01-07T06:00:50.185Z",
    "author": "Kafka推送",
    "summary": "英伟达首席执行官黄仁勋表示，中国对H200 AI芯片需求旺盛...",
    "original": "英伟达(Nvidia)首席执行官黄仁勋(Jensen Huang)表示，中国对该公司H200先进AI处理器的需求“相当高”。一个月前，川普政府做出了批准在中国销售这些芯片的争议性决定。",
    "translation": "",
    "url": "https://www.aboluowang.com/2026/0107/2331339.html",
    "regional_country": ["中国", "美国"],
    "domain": ["科技安全"],
    "topicType": "全球军事信息,规则测试美国"
}



async def test_pipeline():
    print(">>> [Test] Starting Pipeline Test...")
    
    # 1. Initialize Orchestrator
    orchestrator = AgentOrchestrator()
    # We need to manually trigger init because it's usually done in __init__ or run_global_stream
    # But wait, orchestrator.__init__ calls _init_agentscope() which initializes agents.
    # We need to make sure env vars are set for API KEY.
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    
    # Re-init to pick up API Key if needed, or just rely on what's there.
    # Orchestrator __init__ prints "Orchestrator initialized..."
    
    if not orchestrator.agentscope_inited:
        print(">>> [Test] Orchestrator failed to init agents. Check API Key.")
        # Try to force init if possible, or just exit
        # return

    # 2. Simulate PayloadPoller._process_data logic (partially)
    poller = PayloadPoller()
    
    # Map doc to raw_item_dict
    doc = MOCK_DOC
    raw_item_dict = {
        "id": str(doc.get("id")),
        "title": doc.get("title"),
        "summary": doc.get("summary") or doc.get("description") or "",
        "original": doc.get("original"),
        "tags": [],
        "thingId": doc.get("thingId"), # <--- CHECK THIS
        "publishDate": doc.get("publishDate"),
        "source": doc.get("author"),
        "url": doc.get("url"), # <--- CHECK THIS
        "regional_country": doc.get("regional_country"),
        "domain": doc.get("domain"),
        "topicType": doc.get("topicType")
    }
    
    print(f"\n>>> [Step 1] Raw Item Dict prepared:")
    print(f"    thingId: {raw_item_dict.get('thingId')}")
    print(f"    url: {raw_item_dict.get('url')}")
    print(f"    original length: {len(raw_item_dict.get('original'))}")

    # 3. Call Orchestrator Refinement
    print("\n>>> [Step 2] Calling orchestrator.refine_intel_item()...")
    refined_dict = await orchestrator.refine_intel_item(raw_item_dict)
    
    print("\n>>> [Step 3] Refined Dict Result:")
    print(json.dumps(refined_dict, ensure_ascii=False, indent=2))
    
    # 4. Check for 'content' and 'thingId' in Refined Dict
    print("\n>>> [Verification]")
    if refined_dict.get("thingId") == MOCK_DOC["thingId"]:
        print("✅ thingId preserved.")
    else:
        print(f"❌ thingId LOST! Expected {MOCK_DOC['thingId']}, got {refined_dict.get('thingId')}")

    if refined_dict.get("content"):
        print("✅ content field present.")
        print(f"   Content start: {refined_dict['content'][:50]}...")
    else:
        print("❌ content field MISSING or EMPTY!")

    # 5. Simulate DB Mapping
    print("\n>>> [Step 4] Simulating DB Mapping (_dict_to_intel_item)...")
    intel_item = poller._dict_to_intel_item(refined_dict)
    
    if intel_item:
        print(f"    DB Model thing_id: {intel_item.thing_id}")
        print(f"    DB Model content: {intel_item.content[:50] if intel_item.content else 'None'}")
        
        if intel_item.thing_id == MOCK_DOC["thingId"] and intel_item.content:
             print("✅ Pipeline Success!")
        else:
             print("❌ DB Mapping Failed.")
    else:
        print("❌ _dict_to_intel_item returned None.")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
