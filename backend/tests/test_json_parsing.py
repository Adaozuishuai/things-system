import unittest
from app.agent.orchestrator import extract_json_from_text

class TestJsonExtraction(unittest.TestCase):
    def test_standard_markdown(self):
        text = """Here is the data:
```json
[{"title": "Test", "summary": "Info"}]
```
Hope this helps."""
        result = extract_json_from_text(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], "Test")

    def test_raw_list(self):
        text = """Sure, here:
        [
            {"title": "Raw", "summary": "Data"}
        ]
        """
        result = extract_json_from_text(text)
        self.assertEqual(result[0]['title'], "Raw")

    def test_single_object_autowrap(self):
        text = """Found one item:
        {"title": "Single", "summary": "Item"}
        """
        result = extract_json_from_text(text)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]['title'], "Single")

    def test_chinese_punctuation_fix(self):
        text = """[{"title": "中文标题"， "summary": "测试"}]"""  # Note the Chinese comma
        result = extract_json_from_text(text)
        self.assertEqual(result[0]['title'], "中文标题")

    def test_dirty_prefix_suffix(self):
        text = """I found this intel: [{"title": "Dirty"}] verify it."""
        result = extract_json_from_text(text)
        self.assertEqual(result[0]['title'], "Dirty")

if __name__ == '__main__':
    unittest.main()
