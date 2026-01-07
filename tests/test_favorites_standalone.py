import unittest
import requests
import json
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加 backend 路径以导入 app 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, SQLALCHEMY_DATABASE_URL
from app.models import IntelItem, Tag
from app import crud, db_models

# 假设后端运行在 http://127.0.0.1:8000
BASE_URL = "http://127.0.0.1:8000/api/intel"

class TestFavoritesFeature(unittest.TestCase):
    def setUp(self):
        # 1. 直接连接数据库创建测试数据
        # 即使后端正在运行，PostgreSQL 允许并发读取
        # 注意：check_same_thread 是 SQLite 参数，PostgreSQL 不需要
        self.engine = create_engine(SQLALCHEMY_DATABASE_URL)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = TestingSessionLocal()
        
        # 创建一个测试条目
        self.test_id = "test-fav-001"
        self.test_title = "[TEST] 收藏功能测试专用条目"
        
        # 清理可能存在的旧数据
        old_item = self.db.query(db_models.IntelItemDB).filter(db_models.IntelItemDB.id == self.test_id).first()
        if old_item:
            self.db.delete(old_item)
            self.db.commit()
            
        # 插入新数据
        new_item = db_models.IntelItemDB(
            id=self.test_id,
            title=self.test_title,
            summary="这是一个用于测试收藏功能的临时条目。",
            url="http://test.com/1",
            source="TestScript",
            publish_time_str="2024-01-01",
            timestamp=1704067200.0,
            tags=["test"],
            is_hot=False,
            favorited=False # 初始为 False
        )
        self.db.add(new_item)
        self.db.commit()
        print(f"\n[Setup] 数据库预埋测试条目 ID: {self.test_id}")

    def tearDown(self):
        # 清理数据
        item = self.db.query(db_models.IntelItemDB).filter(db_models.IntelItemDB.id == self.test_id).first()
        if item:
            self.db.delete(item)
            self.db.commit()
        self.db.close()

    def test_favorite_lifecycle(self):
        """测试完整的收藏生命周期：收藏 -> 验证 -> 取消收藏 -> 验证"""
        
        item_id = self.test_id
        
        # 1. 初始状态检查
        # 获取详情
        resp = requests.get(f"{BASE_URL}/{item_id}")
        self.assertEqual(resp.status_code, 200)
        item_data = resp.json()
        self.assertFalse(item_data['favorited'], "初始状态应为未收藏")
        print("[Step 1] 初始状态验证通过: 未收藏")
        
        # 2. 执行收藏操作
        print(f"[Step 2] 正在收藏条目 {item_id}...")
        resp = requests.post(f"{BASE_URL}/{item_id}/favorite", json={"favorited": True})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['favorited'], "API 返回状态应为已收藏")
        
        # 3. 验证详情接口状态
        resp = requests.get(f"{BASE_URL}/{item_id}")
        self.assertTrue(resp.json()['favorited'], "详情页状态应为已收藏")
        print("[Step 3] 详情接口验证通过: 已收藏")
        
        # 4. 验证收藏列表接口
        print("[Step 4] 检查收藏列表...")
        resp = requests.get(f"{BASE_URL}/favorites")
        self.assertEqual(resp.status_code, 200)
        favorites = resp.json()['items']
        
        found = any(item['id'] == item_id for item in favorites)
        self.assertTrue(found, "该条目应出现在收藏列表中")
        print(f"[Step 4] 收藏列表验证通过: 列表中包含 ID {item_id}")
        
        # 5. 执行取消收藏操作
        print(f"[Step 5] 正在取消收藏条目 {item_id}...")
        resp = requests.post(f"{BASE_URL}/{item_id}/favorite", json={"favorited": False})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()['favorited'], "API 返回状态应为未收藏")
        
        # 6. 再次验证详情接口
        resp = requests.get(f"{BASE_URL}/{item_id}")
        self.assertFalse(resp.json()['favorited'], "详情页状态应恢复为未收藏")
        print("[Step 6] 详情接口验证通过: 未收藏")
        
        # 7. 再次验证收藏列表
        resp = requests.get(f"{BASE_URL}/favorites")
        favorites = resp.json()['items']
        found = any(item['id'] == item_id for item in favorites)
        self.assertFalse(found, "该条目不应再出现在收藏列表中")
        print("[Step 7] 收藏列表验证通过: 列表中已移除该条目")

if __name__ == '__main__':
    unittest.main()
