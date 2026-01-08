from typing import Optional, Union, List, Dict, Any
from agentscope.agent import AgentBase
from agentscope.message import Msg
from agentscope.model import ChatModelBase
import json
import re
import asyncio
import json
import inspect
from functools import partial

class AnalystAgent(AgentBase):
    """
    分析师智能体 (Analyst Agent)
    
    职责：
    负责根据提供的上下文信息（如检索到的情报）和自身的知识库，
    回答用户的自然语言查询。
    """
    
    def __init__(self, name: str, model: ChatModelBase):
        """
        初始化分析师智能体
        
        参数:
            name: 智能体名称
            model: 用于生成的 LLM 模型实例
        """
        super().__init__()
        self.name = name
        self.model = model
        # 系统提示词，定义智能体的角色和行为准则
        self.sys_prompt = """You are an intelligence analyst. Based on the provided context and your own knowledge, answer the user's query.
        Please answer in Chinese."""

    async def reply(self, x: Optional[Union[Msg, str]] = None) -> Msg:
        """
        生成回复
        
        参数:
            x: 输入消息，可以是 Msg 对象或字符串
            
        返回:
            Msg: 包含回复内容的 Msg 对象
        """
        # 提取输入内容
        content = x.content if isinstance(x, Msg) else x
        
        # 构建消息历史
        messages = [
            {"role": "system", "content": self.sys_prompt},
            {"role": "user", "content": content}
        ]
        
        # 调用模型生成回复
        # 注意：AgentScope 的模型调用通常是同步的，但在 async 方法中调用是可以的
        response = await self.model(messages)
        
        # 提取响应内容
        # 提取响应内容
        answer = ""
        try:
            # Debug: Print response type and dir
            # print(f"DEBUG: Response type: {type(response)}")
            # print(f"DEBUG: Response dir: {dir(response)}")
            
            if isinstance(response, dict) and "text" in response:
                answer = response["text"]
            elif hasattr(response, "text") and response.text:
                answer = response.text
            # Handle ChatResponse object with content list (e.g. from DashScope)
            elif hasattr(response, "content") and isinstance(response.content, list):
                for item in response.content:
                    # Try dict access
                    if isinstance(item, dict) and item.get("type") == "text":
                        answer = item.get("text", "")
                        break
                    # Try attribute access (for objects/Pydantic models)
                    if hasattr(item, "type") and getattr(item, "type") == "text":
                        answer = getattr(item, "text", "")
                        break
                if not answer and response.content:
                     answer = str(response.content)
            else:
                answer = str(response)
        except (KeyError, AttributeError):
            answer = str(response)
        
        return Msg(name=self.name, content=answer, role="assistant")

class DataExtractorAgent(AgentBase):
    """
    数据提取智能体 (DataExtractor Agent)
    
    职责：
    负责从非结构化的原始文本（如新闻、报告）中提取结构化的情报数据。
    核心要求是将提取的内容翻译为中文，并以 JSON 格式输出。
    """
    
    def __init__(self, name: str, model: ChatModelBase):
        """
        初始化提取智能体
        
        参数:
            name: 智能体名称
            model: 用于生成的 LLM 模型实例
        """
        super().__init__()
        self.name = name
        self.model = model
        # 系统提示词，包含严格的输出格式要求和翻译指令
        self.sys_prompt = """CRITICAL REQUIREMENT: Output MUST be valid JSON.
        Extract intelligence items from the text.
        For each item, include: 
        - title: Title of the event
        - summary: Detailed summary of the event
        - date: Date string (YYYY-MM-DD)
        - source: Source of the information
        - tags: List of relevant tags (strings). For countries involved, MUST include the country name in Chinese (e.g., "日本", "美国", "中国") and set its color to "red".
        - is_hot: Boolean indicating if it's a hot topic
        
        CRITICAL: Translate ALL content (title, summary, tags) to CHINESE (Simplified Chinese).
        Ensure the JSON is strictly valid and can be parsed by Python's json.loads().
        Do not include markdown code blocks (```json) if possible, or I will strip them.
        """

    async def reply(self, x: Optional[Union[Msg, str]] = None) -> Msg:
        """
        执行提取任务
        
        参数:
            x: 输入消息，包含待处理的原始文本
            
        返回:
            Msg: 包含提取出的 JSON 字符串的 Msg 对象
        """
        content = x.content if isinstance(x, Msg) else x
        
        messages = [
            {"role": "system", "content": self.sys_prompt},
            {"role": "user", "content": content}
        ]
        
        # 调用模型
        try:
            # 判断 self.model 是否为异步函数
            if asyncio.iscoroutinefunction(self.model) or (hasattr(self.model, "__call__") and asyncio.iscoroutinefunction(self.model.__call__)):
                 response = await self.model(messages)
            else:
                 # 如果是同步调用，则放入 executor
                 loop = asyncio.get_running_loop()
                 response = await loop.run_in_executor(None, partial(self.model, messages))
            
        except Exception as e:
            # print(f"\n❌ [DEBUG] Model Call Failed: {e}")
            raise e
        
        # Handle AsyncGenerator response (Stream)
        if inspect.isasyncgen(response):
            full_content = ""
            async for chunk in response:
                
                # 尝试从 chunk 中提取文本并累积
                chunk_text = ""
                
                # 优先处理 content 列表 (AgentScope 标准格式)
                # 即使 chunk 是 dict，如果它有 content 列表，我们也应该优先解析列表中的 text
                content_list = []
                if hasattr(chunk, "content") and isinstance(chunk.content, list):
                    content_list = chunk.content
                elif isinstance(chunk, dict) and isinstance(chunk.get("content"), list):
                    content_list = chunk.get("content")
                
                if content_list:
                    for item in content_list:
                        if isinstance(item, dict) and item.get("type") == "text":
                            chunk_text += item.get("text", "")
                        elif hasattr(item, "type") and getattr(item, "type") == "text":
                            chunk_text += getattr(item, "text", "")
                
                # 如果没有从 content list 中提取到，尝试其他字段
                if not chunk_text:
                    if isinstance(chunk, dict):
                        # 处理 content 为字符串的情况
                        raw_content = chunk.get("text", "") or chunk.get("content", "")
                        if isinstance(raw_content, str):
                            chunk_text = raw_content
                        # 处理 delta (OpenAI style)
                        if not chunk_text and "choices" in chunk:
                            delta = chunk["choices"][0].get("delta", {})
                            chunk_text = delta.get("content", "")
                    elif hasattr(chunk, "text"):
                        chunk_text = chunk.text
                
                # 如果是增量更新 (Delta)，才需要累积；如果是全量更新 (Full)，则覆盖
                # 观察日志发现 DashScope/AgentScope 返回的是全量更新
                # 因此我们更新 full_content 为当前最长的 chunk_text
                if chunk_text and isinstance(chunk_text, str):
                    if len(chunk_text) > len(full_content):
                        full_content = chunk_text
                    else:
                        # 某些情况下可能是分段的，保守起见，如果看起来像是接续的...
                        # 但针对刚才的日志，明显是覆盖模式。
                        # 简单策略：总是用当前 chunk 覆盖，假设最后一个 chunk 是最完整的
                        full_content = chunk_text
                
                # 保留最后一个 chunk 对象以便后续可能的元数据提取
                response = chunk 
            
            # 如果累积到了内容，构造一个模拟的 dict response
            if full_content:
                response = {"text": full_content}
        
        # 提取响应内容
        answer = ""
        try:
            
            # AgentScope ModelResponse object often behaves like a dict but also has attributes
            if isinstance(response, dict):
                 answer = response.get("text", "")
            
            if not answer and hasattr(response, "text"):
                 answer = response.text
            
            if not answer and hasattr(response, "content"):
                 if isinstance(response.content, list):
                    for item in response.content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            answer = item.get("text", "")
                            break
                        if hasattr(item, "type") and getattr(item, "type") == "text":
                            answer = getattr(item, "text", "")
                            break
                 else:
                    answer = str(response.content)
            
            if not answer:
                answer = str(response)
                
        except Exception as e:
            # print(f"DEBUG: Extraction Error: {e}")
            answer = str(response)
            
        # Regex Fallback if answer is still the raw object representation
        if answer.startswith("ChatResponse") or "ChatResponse(" in answer:
            print("DEBUG: Using Regex Fallback")
            match = re.search(r"'text':\s*'([\s\S]*?)'", str(response))
            if match:
                answer = match.group(1)
                # Basic unescape for the extracted content if needed
                # But usually raw string is fine if it's JSON
                answer = answer.replace("\\n", "\n").replace("\\\"", "\"")
            else:
                # Try double quotes
                match = re.search(r'"text":\s*"([\s\S]*?)"', str(response))
                if match:
                     answer = match.group(1).replace("\\n", "\n").replace("\\\"", "\"")
            
        return Msg(name=self.name, content=answer, role="assistant")

class RefinementAgent(DataExtractorAgent):
    """
    Refinement Agent (情报提炼专家)
    
    职责：
    对单条原始情报进行深度清洗、摘要重写、翻译和智能打标。
    """
    
    def __init__(self, name: str, model: ChatModelBase):
        super().__init__(name, model)
        self.sys_prompt = """
        You are an elite Intelligence Analyst. Your task is to REFINE a single piece of raw intelligence data.

        INPUT: A raw text containing 'title', 'summary', and 'original' text segments.

        TASK:
        1. **Title**: Translate the 'Title' into professional Simplified Chinese.
        2. **Summary**: Translate the provided 'Summary' into Simplified Chinese. Do NOT summarize the 'Original Text'. JUST translate the 'Summary' field provided in input.
        3. **Full Content**: Translate the ENTIRE 'Original Text Snippet' into Simplified Chinese. Maintain the original length, tone, and details.
        4. **Smart Tagging**: Extract relevant tags from the content.
           - **Countries/Regions**: MUST be colored "red" (e.g., {"label": "美国", "color": "red"}).
           - **Domains**: MUST be colored "blue" (e.g., {"label": "军事安全", "color": "blue"}, {"label": "政治外交", "color": "blue"}).
           - **Keywords**: Can be colored "gray".

        OUTPUT FORMAT (Strict JSON):
        {
            "title": "精炼后的中文标题",
            "summary": "翻译后的中文摘要 (对应输入的 Summary 字段)",
            "content": "全文翻译后的内容 (对应输入的 Original Text Snippet 字段)...",
            "tags": [
                {"label": "美国", "color": "red"},
                {"label": "委内瑞拉", "color": "red"},
                {"label": "军事冲突", "color": "blue"}
            ]
        }
        
        CRITICAL: 
        - Output ONLY valid JSON.
        """

    async def reply(self, x: Optional[Union[Msg, str]] = None) -> Msg:
        """
        重写 reply 方法，增加 Mock Fallback 机制
        """
        try:
            # 尝试正常调用 LLM
            return await super().reply(x)
        except Exception as e:
            print(f"RefinementAgent LLM Error: {e}. Using Mock Fallback.")
            # Mock Fallback Logic
            content = x.content if isinstance(x, Msg) else x
            
            # Simple heuristic extraction
            # Try to extract title from input (assuming input format "Title: ... Summary: ...")
            title_match = re.search(r"Title:\s*(.*?)\n", content)
            summary_match = re.search(r"Summary:\s*(.*?)\n", content)
            original_match = re.search(r"Original Text Snippet:\s*([\s\S]*)", content)
            
            title = title_match.group(1).strip() if title_match else "未知标题"
            summary = summary_match.group(1).strip() if summary_match else "暂无摘要"
            original_text = original_match.group(1).strip() if original_match else content
            
            # Simulated Translation & Tagging
            mock_json = {
                "title": title,
                "summary": f"{summary}",
                "content": original_text, # Fallback to extracted original content
                "tags": [
                    {"label": "系统降级", "color": "gray"}
                ]
            }
            
            return Msg(name=self.name, content=json.dumps(mock_json, ensure_ascii=False), role="assistant")
