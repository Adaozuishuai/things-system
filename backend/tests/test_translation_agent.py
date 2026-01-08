import os
import sys
import asyncio
import json
import inspect
from dotenv import load_dotenv

# Add backend directory to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(backend_path)

# Load .env
env_path = os.path.join(backend_path, '.env')
load_dotenv(env_path)

# Import AgentScope
try:
    import agentscope
    from agentscope.model import DashScopeChatModel
    from agentscope.message import Msg
    from agentscope.agent import AgentBase
except ImportError:
    print("AgentScope not installed.")
    sys.exit(1)

# Custom Translation Agent
class TranslationAgent(AgentBase):
    def __init__(self, name: str, model):
        super().__init__()
        self.name = name
        self.model = model
        self.sys_prompt = """
        你是一位专业翻译。你的任务是将用户提供的文本翻译成简体中文。
        
        要求：
        1. 如果原文已经是中文，请原样输出，不要做任何修改。
        2. 如果原文是其他语言（如英文），请翻译成流畅、准确的简体中文。
        3. **保持原文的篇幅和细节**，不要进行摘要或缩写。
        4. 这是一个翻译任务，不是总结任务。
        5. 只输出翻译后的内容，不要包含任何解释性文字。
        """

    async def reply(self, x: Msg) -> Msg:
        content = x.content
        messages = [
            {"role": "system", "content": self.sys_prompt},
            {"role": "user", "content": content}
        ]
        
        try:
            response = await self.model(messages)
            
            # Handle Streaming (AsyncGenerator)
            if inspect.isasyncgen(response):
                final_res = None
                async for chunk in response:
                    final_res = chunk
                response = final_res
            
            # Handle response extraction (AgentScope/DashScope specific)
            answer = ""
            
            # Safe attribute access
            try:
                if hasattr(response, "text") and response.text:
                    answer = response.text
            except (AttributeError, KeyError):
                pass
            
            if not answer:
                if isinstance(response, dict):
                     answer = response.get("text", "")
            
            # Fallback for complex structures
            if not answer and hasattr(response, "content"):
                 # Simple extraction from content list
                 try:
                     content_list = response.content
                     if isinstance(content_list, list) and len(content_list) > 0:
                         item = content_list[0]
                         if isinstance(item, dict):
                             answer = item.get("text", "")
                         elif hasattr(item, "text"):
                             answer = item.text
                 except Exception:
                     pass

            if not answer:
                # Try regex on string representation as last resort
                import re
                match = re.search(r"'text':\s*'([\s\S]*?)'", str(response))
                if match:
                    answer = match.group(1)
            
            if not answer:
                answer = str(response)

            return Msg(name=self.name, content=answer, role="assistant")
            
        except Exception as e:
            return Msg(name=self.name, content=f"Error: {str(e)}", role="assistant")

def repair_json(json_str):
    """
    Naive JSON repair tool to handle unescaped control characters
    """
    new_str = []
    in_string = False
    escape = False
    for char in json_str:
        if char == '"' and not escape:
            in_string = not in_string
        
        if char == '\\':
            escape = not escape
        else:
            escape = False
            
        if in_string:
            if char == '\n':
                new_str.append('\\n')
            elif char == '\r':
                pass
            elif char == '\t':
                new_str.append('\\t')
            # Handle other control chars if needed, but usually \n is the culprit
            elif ord(char) < 32:
                 pass 
            else:
                new_str.append(char)
        else:
            new_str.append(char)
    return "".join(new_str)

async def test_translation():
    print(">>> [Test] Initializing AgentScope...")
    agentscope.init(project="TranslationTest")

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print(">>> [Error] API Key not found.")
        return

    # Initialize Model (using qwen-plus for better cost/performance balance)
    model = DashScopeChatModel(
        config_name="translation-model",
        model_name="qwen-plus",
        api_key=api_key,
        generate_args={"temperature": 0.3} # Lower temperature for more faithful translation
    )

    # Initialize Agent
    translator = TranslationAgent(name="Translator", model=model)

    # Load Data
    data_path = "/home/system_/system_mvp/data.json"
    print(f">>> [Test] Loading data from {data_path}...")
    
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            raw_content = f.read()
            
        try:
            data = json.loads(raw_content)
        except json.JSONDecodeError as e:
            print(f">>> [Warning] Standard JSON parse failed: {e}. Attempting repair...")
            fixed_content = repair_json(raw_content)
            try:
                data = json.loads(fixed_content)
                print(">>> [Success] JSON repaired successfully.")
            except json.JSONDecodeError as e:
                print(f">>> [Error] Repair failed: {e}")
                # Fallback: Extract 'original' field via regex
                import re
                print(">>> [Info] Attempting regex extraction...")
                # Try simple regex looking for "original": "..."
                # We need to be careful about escaped quotes inside the string
                match = re.search(r'"original"\s*:\s*"(.*?)"\s*(?:,|\})', raw_content, re.DOTALL)
                if match:
                    # Need to unescape manually
                    extracted = match.group(1)
                    # This might still have issues if there are unescaped quotes, but worth a shot
                    data = {"original": extracted}
                else:
                    print("DEBUG: Regex failed to match.")
                    return

        original_text = data.get("original", "")
        if not original_text:
            print(">>> [Error] 'original' field is empty or missing.")
            return

        print(f"\n>>> [Input] Original Text ({len(original_text)} chars):")
        print("-" * 50)
        print(original_text[:500] + "..." if len(original_text) > 500 else original_text)
        print("-" * 50)

        # Call Agent
        print("\n>>> [Test] Translating...")
        msg = Msg(name="User", content=original_text, role="user")
        response = await translator.reply(msg)

        print(f"\n>>> [Output] Translated Text ({len(str(response.content))} chars):")
        print("=" * 50)
        print(response.content)
        print("=" * 50)

    except FileNotFoundError:
        print(f">>> [Error] File not found: {data_path}")
    except json.JSONDecodeError:
        print(f">>> [Error] Invalid JSON in {data_path}")
    except Exception as e:
        print(f">>> [Error] {e}")

if __name__ == "__main__":
    asyncio.run(test_translation())
