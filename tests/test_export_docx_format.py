import io
import os
import sys
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from docx import Document

from app import db_models
from app.agent.orchestrator import orchestrator
from app.database import SessionLocal
from app.models import ExportRequest
from app.routes.intel import export_intel


def _read_doc_texts(docx_bytes: bytes):
    doc = Document(io.BytesIO(docx_bytes))
    return [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]


def _assert_doc_texts(texts, title: str, content: str, tags_line: str):
    if not texts:
        raise AssertionError("exported doc has no paragraphs")

    if texts[0] != tags_line:
        raise AssertionError(f"unexpected 栏目行: {texts[0]!r}")
    if not texts[1].startswith("事件时间："):
        raise AssertionError(f"unexpected 时间行: {texts[1]!r}")
    if not texts[2].startswith("价值点："):
        raise AssertionError(f"unexpected 价值点行: {texts[2]!r}")

    if title not in texts:
        raise AssertionError(f"missing 标题 in paragraphs: {texts!r}")
    if content not in texts:
        raise AssertionError(f"missing 正文 in paragraphs: {texts!r}")

    tail = texts[-1]
    if not tail.startswith("（来源："):
        raise AssertionError(f"unexpected 来源行: {tail!r}")
    if f"原标题：{title}" not in tail:
        raise AssertionError(f"missing 原标题 in 来源行: {tail!r}")


def run_db_item_test():
    test_id = f"test-export-db-{uuid.uuid4().hex}"
    db = SessionLocal()
    try:
        db.query(db_models.IntelItemDB).filter(db_models.IntelItemDB.id == test_id).delete()
        db.commit()

        db.add(
            db_models.IntelItemDB(
                id=test_id,
                title="标题DB",
                summary="价值点DB",
                content="正文DB",
                source="DB 来源",
                url="https://example.com/db",
                publish_time_str="2025/08/01 00:00",
                timestamp=1.0,
                tags=[{"label": "日本", "color": "red"}, {"label": "军事安全", "color": "blue"}],
                is_hot=False,
                favorited=False,
            )
        )
        db.commit()

        req = ExportRequest(ids=[test_id])
        res = __import__("asyncio").run(export_intel(req, db))
        body = getattr(res, "body", None)
        if not body:
            raise AssertionError("missing export response body")

        texts = _read_doc_texts(body)
        _assert_doc_texts(texts, title="标题DB", content="正文DB", tags_line="拟投栏目：日本 / 军事安全")

        if "来源URL：https://example.com/db" not in texts[-1]:
            raise AssertionError(f"missing 来源URL in 来源行: {texts[-1]!r}")
    finally:
        db.query(db_models.IntelItemDB).filter(db_models.IntelItemDB.id == test_id).delete()
        db.commit()
        db.close()


def run_cache_item_fallback_test():
    test_id = f"test-export-cache-{uuid.uuid4().hex}"
    db = SessionLocal()
    try:
        db.query(db_models.IntelItemDB).filter(db_models.IntelItemDB.id == test_id).delete()
        db.commit()

        orchestrator.global_cache.append(
            {
                "id": test_id,
                "title": "标题CACHE",
                "summary": "价值点CACHE",
                "content": "正文CACHE",
                "source": "CACHE 来源",
                "url": "https://example.com/cache",
                "time": "2025/08/02 00:00",
                "timestamp": 2.0,
                "tags": [{"label": "美国", "color": "red"}, {"label": "政治外交", "color": "blue"}],
                "favorited": False,
                "is_hot": True,
            }
        )

        req = ExportRequest(ids=[test_id])
        res = __import__("asyncio").run(export_intel(req, db))
        body = getattr(res, "body", None)
        if not body:
            raise AssertionError("missing export response body")

        texts = _read_doc_texts(body)
        _assert_doc_texts(texts, title="标题CACHE", content="正文CACHE", tags_line="拟投栏目：美国 / 政治外交")

        if "来源URL：https://example.com/cache" not in texts[-1]:
            raise AssertionError(f"missing 来源URL in 来源行: {texts[-1]!r}")

        row = db.query(db_models.IntelItemDB).filter(db_models.IntelItemDB.id == test_id).first()
        if not row:
            raise AssertionError("cached item not persisted to DB during export fallback")
    finally:
        try:
            for x in list(orchestrator.global_cache):
                if isinstance(x, dict) and x.get("id") == test_id:
                    orchestrator.global_cache.remove(x)
                    break
        except Exception:
            pass

        db.query(db_models.IntelItemDB).filter(db_models.IntelItemDB.id == test_id).delete()
        db.commit()
        db.close()


if __name__ == "__main__":
    run_db_item_test()
    run_cache_item_fallback_test()

