import os
import sys
import time
from datetime import datetime

import requests


def main():
    base_url = os.getenv("BASE_URL", "http://127.0.0.1:8001")
    api_base = base_url.rstrip("/") + "/api"

    now = datetime.now()
    items = []
    for i in range(5):
        ts = now.timestamp() + i
        item_id = f"ui-test-{int(now.timestamp())}-{i+1}"
        items.append(
            {
                "id": item_id,
                "title": f"UI 测试消息 {i+1}",
                "summary": f"用于验证新消息是否置顶（{i+1}/5）",
                "source": "UI Test",
                "url": None,
                "time": now.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": ts,
                "tags": [{"label": "UI测试", "color": "gray"}],
                "favorited": False,
                "is_hot": True,
            }
        )

    endpoint = api_base + "/agent/debug/broadcast"
    for item in items:
        resp = requests.post(endpoint, json={"event": "new_intel", "data": item}, timeout=5)
        if resp.status_code != 200:
            print(f"FATAL: debug broadcast failed {resp.status_code}: {resp.text}")
            sys.exit(1)
        time.sleep(0.05)

    newest = max(items, key=lambda x: float(x.get("timestamp") or 0))
    print("Injected 5 items successfully.")
    print("Expected TOP item (newest timestamp):")
    print(f"  id={newest['id']}, title={newest['title']}, ts={newest['timestamp']}")
    print("Now open 热点页，刷新后应看到这条在最上面。")


if __name__ == "__main__":
    main()

