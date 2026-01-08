import os
import sys
import time
import uuid


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.agent.orchestrator import orchestrator
from app import crud
from app.database import SessionLocal
from app.models import FavoriteToggleRequest
from app.routes.intel import toggle_favorite
from app import db_models


def run_test():
    test_id = f"test-fav-{uuid.uuid4().hex}"

    orchestrator.global_cache.append(
        {
            "id": test_id,
            "title": "t",
            "summary": "s",
            "source": "Hot Stream",
            "url": "https://example.com",
            "time": "2026/01/01 00:00",
            "timestamp": 0,
            "tags": [{"label": "x", "color": "blue"}],
            "favorited": False,
            "is_hot": True,
        }
    )

    db = SessionLocal()
    try:
        db.query(db_models.IntelItemDB).filter(db_models.IntelItemDB.id == test_id).delete()
        db.commit()

        req = FavoriteToggleRequest(favorited=True)
        result = __import__("asyncio").run(toggle_favorite(test_id, req, db))

        if not result or result.id != test_id or result.favorited is not True:
            raise AssertionError(f"unexpected result: {result}")

        row = db.query(db_models.IntelItemDB).filter(db_models.IntelItemDB.id == test_id).first()
        if not row:
            raise AssertionError("item not persisted to DB")
        if row.favorited is not True:
            raise AssertionError("DB favorited not updated")
    finally:
        db.query(db_models.IntelItemDB).filter(db_models.IntelItemDB.id == test_id).delete()
        db.commit()
        db.close()


def run_history_insertion_order_test():
    first_id = f"test-history-1-{uuid.uuid4().hex}"
    second_id = f"test-history-2-{uuid.uuid4().hex}"

    db = SessionLocal()
    try:
        db.query(db_models.IntelItemDB).filter(db_models.IntelItemDB.id.in_([first_id, second_id])).delete()
        db.commit()

        db.add(
            db_models.IntelItemDB(
                id=first_id,
                title="first",
                summary="first",
                source="test",
                publish_time_str="",
                timestamp=9999999999.0,
                tags=[],
                is_hot=False,
                favorited=False,
            )
        )
        db.commit()

        time.sleep(1.1)

        db.add(
            db_models.IntelItemDB(
                id=second_id,
                title="second",
                summary="second",
                source="test",
                publish_time_str="",
                timestamp=1.0,
                tags=[],
                is_hot=False,
                favorited=False,
            )
        )
        db.commit()

        items, _ = crud.get_filtered_intel(db, type_filter="history", limit=10, offset=0)
        ids = [i.id for i in items]
        if second_id not in ids or first_id not in ids:
            raise AssertionError(f"missing ids in results: {ids!r}")

        if ids[0] != second_id:
            raise AssertionError(f"expected newest inserted history item first, got order: {ids!r}")
    finally:
        db.query(db_models.IntelItemDB).filter(db_models.IntelItemDB.id.in_([first_id, second_id])).delete()
        db.commit()
        db.close()


if __name__ == "__main__":
    run_test()
    run_history_insertion_order_test()
