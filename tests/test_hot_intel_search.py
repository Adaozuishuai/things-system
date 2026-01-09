import os
import sys
import time
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app import db_models
from app import crud
from app.database import SessionLocal
from app.models import IntelItem, Tag


def run_test():
    db = SessionLocal()
    test_ids = []
    now = time.time()
    try:
        hot_a_id = f"test-hot-{uuid.uuid4()}"
        hot_b_id = f"test-hot-{uuid.uuid4()}"
        hot_old_id = f"test-hot-{uuid.uuid4()}"
        history_id = f"test-his-{uuid.uuid4()}"
        test_ids.extend([hot_a_id, hot_b_id, hot_old_id, history_id])

        crud.create_intel_item(
            db,
            IntelItem(
                id=hot_a_id,
                title="黄仁勋：中国对辉达AI芯片需求相当高",
                summary="英伟达首席执行官表示需求旺盛",
                source="Kafka推送",
                url="https://example.com/a",
                time="2026-01-07",
                timestamp=now,
                tags=[Tag(label="科技安全", color="blue")],
                favorited=False,
                is_hot=True,
                content=None,
                thing_id=None,
            ),
        )
        crud.create_intel_item(
            db,
            IntelItem(
                id=hot_b_id,
                title="苹果发布新产品",
                summary="发布会内容摘要",
                source="Kafka推送",
                url="https://example.com/b",
                time="2026-01-07",
                timestamp=now,
                tags=[Tag(label="科技", color="blue")],
                favorited=False,
                is_hot=True,
                content=None,
                thing_id=None,
            ),
        )
        crud.create_intel_item(
            db,
            IntelItem(
                id=hot_old_id,
                title="旧热点：不会出现在12小时内搜索",
                summary="旧热点摘要",
                source="Kafka推送",
                url="https://example.com/old",
                time="2026-01-01",
                timestamp=now - 13 * 3600,
                tags=[Tag(label="旧闻", color="gray")],
                favorited=False,
                is_hot=True,
                content=None,
                thing_id=None,
            ),
        )
        crud.create_intel_item(
            db,
            IntelItem(
                id=history_id,
                title="历史情报：黄仁勋 相关",
                summary="历史摘要",
                source="Kafka推送",
                url="https://example.com/his",
                time="2026-01-07",
                timestamp=now,
                tags=[Tag(label="历史", color="gray")],
                favorited=False,
                is_hot=False,
                content=None,
                thing_id=None,
            ),
        )

        items, total = crud.get_filtered_intel(db, type_filter="hot", q="黄仁勋", range_filter="all", limit=50, offset=0)
        assert total >= 1
        ids = {x.id for x in items}
        assert hot_a_id in ids
        assert history_id not in ids

        items_12h, _ = crud.get_filtered_intel(db, type_filter="hot", q="", range_filter="12h", limit=200, offset=0)
        ids_12h = {x.id for x in items_12h}
        assert hot_old_id not in ids_12h
        assert hot_a_id in ids_12h

        print("PASS: hot intel search filtering works")
    finally:
        try:
            db.query(db_models.IntelItemDB).filter(db_models.IntelItemDB.id.in_(test_ids)).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()


if __name__ == "__main__":
    run_test()

