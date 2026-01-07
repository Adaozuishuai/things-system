import unittest
import asyncio
import uuid
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量 (确保能读到 API Key)
load_dotenv()

from app.agent.orchestrator import AgentOrchestrator
from app.database import SessionLocal
from app.db_models import IntelItemDB
from app import crud
from app.models import IntelItem

class TestIntegrationPipeline(unittest.TestCase):
    def setUp(self):
        self.orchestrator = AgentOrchestrator()
        self.db = SessionLocal()
        # 生成一个唯一的测试 ID，避免冲突
        self.test_id = str(uuid.uuid4())
        
        # 构造模拟的 API 推送数据
        self.raw_item = {
            "id": self.test_id,
            "title": "Integration Test: SpaceX Launch",
            "summary": "SpaceX successfully launched Starship from Texas. 埃隆·马斯克表示任务成功。",
            "original": "SpaceX Starship launch successful. Weather was good.",
            "tags": ["SpaceX", "USA", "Technology"],
            "publishDate": datetime.now().isoformat(),
            "source": "TestScript",
            "url": "http://test.com/spacex"
        }

    def tearDown(self):
        # 清理测试数据
        try:
            item = self.db.query(IntelItemDB).filter(IntelItemDB.id == self.test_id).first()
            if item:
                self.db.delete(item)
                self.db.commit()
                print(f"\n🧹 测试数据已清理: {self.test_id}")
        finally:
            self.db.close()

    def test_pipeline_flow(self):
        """测试完整流程：提炼 -> 打印 -> 入库验证"""
        
        print("\n🚀 开始测试完整数据流水线...")
        
        # 1. 提炼 (Refinement)
        print("1️⃣  正在调用 Orchestrator 进行智能提炼...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        refined_dict = loop.run_until_complete(self.orchestrator.refine_intel_item(self.raw_item))
        loop.close()
        
        # 2. 打印提炼后的数据
        print("\n📄 提炼后的数据 (Refined Data):")
        print("-" * 40)
        print(f"ID:      {refined_dict['id']}")
        print(f"Title:   {refined_dict['title']}")
        print(f"Summary: {refined_dict['summary']}")
        print(f"Tags:    {refined_dict['tags']}")
        print("-" * 40)
        
        # 3. 转换模型
        # 手动补全 IntelItem 所需字段
        try:
            # 1. 处理时间
            now = datetime.now()
            refined_dict["time"] = now.strftime("%Y/%m/%d %H:%M")
            refined_dict["timestamp"] = now.timestamp()
            
            # 2. 处理标签 (从字符串/字典转换为 Tag 对象列表)
            # Orchestrator 返回的 tags 可能是字符串列表，也可能是字典列表(如果 LLM 正常工作)
            raw_tags = refined_dict.get("tags", [])
            tag_objects = []
            for t in raw_tags:
                if isinstance(t, str):
                    tag_objects.append({"label": t, "color": "gray"})
                elif isinstance(t, dict):
                    tag_objects.append(t)
            refined_dict["tags"] = tag_objects
            
            intel_item = IntelItem(**refined_dict)
        except Exception as e:
            self.fail(f"❌ 数据模型转换失败: {e}")

        # 4. 入库 (Ingestion)
        print("\n2️⃣  正在存入数据库...")
        try:
            crud.create_intel_item(self.db, intel_item)
            print("✅ 入库操作执行成功")
        except Exception as e:
            self.fail(f"❌ 入库失败: {e}")

        # 5. 验证 (Verification)
        print("\n3️⃣  正在从数据库查询以验证...")
        db_item = crud.get_intel_by_id(self.db, self.test_id)
        
        self.assertIsNotNone(db_item, "❌ 数据库中未找到该记录！")
        self.assertEqual(db_item.id, self.test_id, "❌ ID 不匹配")
        self.assertEqual(db_item.title, refined_dict['title'], "❌ 标题不匹配")
        
        print(f"✅ 验证成功！数据库中存在记录: {db_item.title}")
        print("🎉 完整流水线测试通过！")

if __name__ == '__main__':
    unittest.main()
