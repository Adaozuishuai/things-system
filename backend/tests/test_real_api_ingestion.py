import unittest
import asyncio
import os
import aiohttp
import json
import sys

# 将 backend 目录添加到 sys.path，解决 ModuleNotFoundError
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from app.services.payload_poller import PayloadPoller
from app.agent.orchestrator import AgentOrchestrator
from app.database import SessionLocal
from app import crud
from app.models import IntelItem

class TestRealAPIIngestion(unittest.TestCase):
    def setUp(self):
        # 1. 配置 Poller
        self.poller = PayloadPoller()
        self.cms_url = os.getenv("CMS_URL")
        self.collection = os.getenv("CMS_COLLECTION", "articles")
        self.email = os.getenv("CMS_EMAIL")
        self.password = os.getenv("CMS_PASSWORD")
        
        if not all([self.cms_url, self.email, self.password]):
            self.skipTest("❌ 缺少 CMS 环境变量配置，跳过真实 API 测试")
            
        self.poller.configure(
            cms_url=self.cms_url,
            collection_slug=self.collection,
            email=self.email,
            password=self.password
        )
        
        self.orchestrator = AgentOrchestrator()
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()
        # 清理 Poller session
        if self.poller.session and not self.poller.session.closed:
            # 创建一个新的临时 loop 来运行 close，或者在测试主 loop 中处理
            # 由于 unittest 的 tearDown 是同步的，这里处理 async 比较麻烦
            # 我们尽量在 test 方法内部的 finally 块中处理资源清理
            pass

    def test_real_fetch_and_store(self):
        """测试：从真实 API 拉取 -> 打印 -> 提炼 -> 入库"""
        
        async def run_test():
            try:
                print(f"\n🌍 正在连接 CMS: {self.cms_url}")
                
                # 1. 登录
                login_success = await self.poller._login()
                self.assertTrue(login_success, "❌ CMS 登录失败")
                print("✅ 登录成功")
                
                # ... (省略中间代码) ...
                
                # 2. 拉取数据
                fetch_url = f"{self.cms_url}/api/{self.collection}"
                headers = {"Authorization": f"JWT {self.poller.token}"}
                
                print(f"📥 正在拉取数据: {fetch_url}")
                async with self.poller.session.get(fetch_url, headers=headers) as response:
                    self.assertEqual(response.status, 200, f"❌ 拉取失败: {response.status}")
                    data = await response.json()
                    
                docs = data.get("docs", [])
                print(f"📦 拉取到 {len(docs)} 条数据")
                
                if not docs:
                    print("⚠️  CMS 中没有数据，测试结束")
                    return

                # 3. 打印第一条原始数据
                raw_doc = docs[0]
                print("\n📄 [原始数据 Sample] (From API):")
                print("-" * 40)
                print(json.dumps(raw_doc, indent=2, ensure_ascii=False)[:1000] + "...") 
                print("-" * 40)
                
                # 4. 提炼 (Refine)
                print("\n🧠 正在调用 AI 进行提炼...")
                raw_item_dict = {
                    "id": str(raw_doc.get("id")),
                    "title": raw_doc.get("title") or "Untitled",
                    "summary": raw_doc.get("summary") or raw_doc.get("description") or "",
                    "original": raw_doc.get("original") or raw_doc.get("content") or "",
                    "tags": [],
                    "publishDate": raw_doc.get("publishDate") or raw_doc.get("createdAt"),
                    "source": raw_doc.get("author") or "PayloadCMS",
                    "url": f"{self.cms_url}/admin/collections/{self.collection}/{raw_doc.get('id')}"
                    
                }
                
                refined_dict = await self.orchestrator.refine_intel_item(raw_item_dict)
                
                print("\n✨ [提炼后数据] (Refined):")
                print("-" * 40)
                print(f"Title:   {refined_dict['title']}")
                print(f"Summary: {refined_dict['summary']}")
                print(f"Tags:    {refined_dict['tags']}")
                print("-" * 40)
                
                # 5. 入库 (Store)
                item_model = self.poller._dict_to_intel_item(refined_dict)
                
                if item_model:
                    print(f"\n💾 正在存入数据库 (ID: {item_model.id})...")
                    existing = crud.get_intel_by_id(self.db, item_model.id)
                    if not existing:
                        crud.create_intel_item(self.db, item_model)
                        print("✅ 新增成功")
                    else:
                        print("⚠️  记录已存在，跳过新增")
                        
                    # 6. 验证 (Verify)
                    db_item = crud.get_intel_by_id(self.db, item_model.id)
                    self.assertIsNotNone(db_item)
                    print(f"✅ 数据库验证通过: 查找到标题为 '{db_item.title}' 的记录")
                    
                    # ==========================================
                    # 7. 测试收藏功能 (Test Favorites)
                    # ==========================================
                    print(f"\n❤️  正在测试收藏功能 (ID: {db_item.id})...")
                    
                    # 7.1 初始状态检查 (Initial Check)
                    self.assertFalse(db_item.favorited, "❌ 初始收藏状态应为 False")
                    print("✅ 初始状态: 未收藏")
                    
                    # 7.2 执行收藏 (Favorite)
                    print("👉 执行收藏操作...")
                    crud.toggle_favorite(self.db, db_item.id, True)
                    
                    # 重新从 DB 获取以验证
                    db_item_fav = crud.get_intel_by_id(self.db, db_item.id)
                    self.assertTrue(db_item_fav.favorited, "❌ 收藏操作失败: 状态仍为 False")
                    print("✅ 收藏成功: 状态变为 True")
                    
                    # 7.3 验证 get_favorites 列表 (Verify List)
                    print("🔍 验证收藏列表...")
                    fav_items, total = crud.get_favorites(self.db)
                    is_in_list = any(item.id == db_item.id for item in fav_items)
                    self.assertTrue(is_in_list, "❌ 收藏列表中未找到该项目")
                    print(f"✅ 列表验证通过: 当前共有 {total} 条收藏")
                    
                    # 7.4 取消收藏 (Unfavorite)
                    print("👉 执行取消收藏操作...")
                    crud.toggle_favorite(self.db, db_item.id, False)
                    
                    db_item_unfav = crud.get_intel_by_id(self.db, db_item.id)
                    self.assertFalse(db_item_unfav.favorited, "❌ 取消收藏失败: 状态仍为 True")
                    print("✅ 取消收藏成功: 状态恢复为 False")
                    
                else:
                    self.fail("❌ 模型转换失败")

            finally:
                # 显式关闭 Session
                if self.poller.session:
                    await self.poller.session.close()
                # 给一点时间让底层连接断开
                await asyncio.sleep(0.1)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_test())
        loop.close()

if __name__ == '__main__':
    unittest.main()
