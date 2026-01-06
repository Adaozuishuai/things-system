import asyncio
import uuid
import json
import os
import inspect
from typing import AsyncGenerator, Dict, Any, List
from collections import deque
from app.models import AgentSearchRequest, AgentSearchResponse
from app.database import SessionLocal
from app import crud, db_models
from app.agent import config as agent_config
from app.agent.agents import AnalystAgent, DataExtractorAgent, RefinementAgent

# AgentScope 导入部分
# 尝试导入 AgentScope 库，如果环境未安装则设置标志位，避免程序崩溃
try:
    import agentscope
    from agentscope.message import Msg
    from agentscope.model import DashScopeChatModel
    AGENTSCOPE_AVAILABLE = True
except ImportError:
    AGENTSCOPE_AVAILABLE = False

import re
import json

def extract_json_from_text(text: str):
    """
    从文本中健壮地提取 JSON 数据
    支持提取 markdown 代码块、最外层列表/对象，并进行简单的字符修复
    """
    # 0. 尝试直接解析
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    json_str = ""
    # 1. 优先尝试匹配 Markdown 代码块
    match = re.search(r"```json\s*([\s\S]*?)\s*```", text)
    if match:
        json_str = match.group(1)
    else:
        # 2. 尝试匹配最外层的 [] (因为预期返回列表)
        # 使用 ^ 和 $ 确保匹配整个结构，或者非贪婪匹配
        # 实际上如果上面的直接解析失败了，说明 text 不纯是 JSON
        # 那么我们尝试提取
        
        # 尝试提取 JSON 对象 {}
        match_obj = re.search(r"\{[\s\S]*\}", text)
        # 尝试提取 JSON 数组 []
        match_arr = re.search(r"\[[\s\S]*\]", text)
        
        # 比较哪个匹配更长/更早
        # 这里为了兼容之前的逻辑（优先列表），我们先看列表
        # 但如果列表在对象内部（RefinementAgent的情况），我们应该优先对象
        
        if match_obj and (not match_arr or len(match_obj.group(0)) > len(match_arr.group(0))):
             json_str = match_obj.group(0)
        elif match_arr:
             json_str = match_arr.group(0)
        else:
             json_str = text

    try:
        return json.loads(json_str.strip())
    except json.JSONDecodeError:
        # 尝试简单的字符替换修复 (中文标点)
        try:
            fixed_str = json_str.replace("，", ",").replace("“", '"').replace("”", '"')
            return json.loads(fixed_str)
        except json.JSONDecodeError:
            # Last ditch: try to fix single quotes to double quotes if valid json otherwise
            try:
                fixed_str = json_str.replace("'", '"')
                return json.loads(fixed_str)
            except:
                pass
            raise

class AgentOrchestrator:
    """
    智能体编排器 (Agent Orchestrator)
    负责管理和调度所有的智能体任务，包括用户查询处理和后台数据分析。
    """
    
    def __init__(self):
        """
        初始化编排器
        - tasks: 用于存储异步任务的状态和结果
        - agentscope_inited: 标记 AgentScope 是否已成功初始化
        - analyst_agent: 用于回答用户查询的分析师智能体
        - extractor_agent: 用于处理原始数据的数据提取智能体
        """
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.agentscope_inited = False
        self.analyst_agent = None
        self.extractor_agent = None
        self.refinement_agent = None
        
        # Global Stream Caching
        self.global_queues: List[asyncio.Queue] = []
        self.global_cache = deque(maxlen=100)
        print("Orchestrator initialized, cache empty")
        
        # 初始化 AgentScope 环境和智能体
        self._init_agentscope()

    def _init_agentscope(self):
        """
        初始化 AgentScope 环境及相关模型配置
        如果 AgentScope 库不可用，则跳过初始化。
        """
        if not AGENTSCOPE_AVAILABLE:
            return
            
        try:
            # 1. 初始化 AgentScope (主要用于日志记录配置)
            # project 参数用于区分不同的项目日志
            agentscope.init(project="IntelAgent")
            
            # 2. 直接初始化 DashScope 模型实例
            # 从 config 中获取配置，或直接使用默认值
            model_config_name = "dashscope-chat"
            dashscope_model = DashScopeChatModel(
                config_name=model_config_name,
                model_name="qwen-max", # 使用通义千问 Max 模型
                api_key=agent_config.DASHSCOPE_API_KEY, # 从环境变量或 config 获取
                generate_args={
                    "temperature": 0.5, # 控制生成的随机性
                }
            )

            # 4. 实例化智能体
            self.analyst_agent = AnalystAgent(
                name="Analyst",
                model=dashscope_model
            )
            self.extractor_agent = DataExtractorAgent(
                name="Extractor",
                model=dashscope_model
            )
            self.refinement_agent = RefinementAgent(
                name="Refiner",
                model=dashscope_model
            )
            
            self.agentscope_inited = True
            print("AgentScope inited successfully with DashScope model.")
            
        except Exception as e:
            # 如果初始化失败，打印错误并标记初始化失败
            print(f"AgentScope Init Error: {e}")
            self.agentscope_inited = False

    async def broadcast(self, event_type: str, data: Any):
        """
        Broadcast event to all connected clients
        """
        # Add to cache if it's new intel
        if event_type == "new_intel":
            self.global_cache.append(data)
            
        if not self.global_queues:
            print(f"Broadcast {event_type}: No connected clients")
            return
            
        message = f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        print(f"Broadcasting {event_type} to {len(self.global_queues)} clients")
        
        for q in self.global_queues:
            await q.put(message)

    async def run_global_stream(self) -> AsyncGenerator[str, None]:
        """
        Global SSE stream for real-time updates
        """
        print("New global stream connection request")
        queue = asyncio.Queue()
        self.global_queues.append(queue)
        print(f"Client connected. Total clients: {len(self.global_queues)}")
        
        try:
            # 1. Send initial batch from cache
            if self.global_cache:
                initial_data = list(self.global_cache)
                yield f"event: initial_batch\ndata: {json.dumps(initial_data, ensure_ascii=False)}\n\n"
            
            # 2. Stream new events
            while True:
                message = await queue.get()
                yield message
        except asyncio.CancelledError:
            pass
        finally:
            if queue in self.global_queues:
                self.global_queues.remove(queue)

    def create_task(self, request: AgentSearchRequest) -> str:
        """
        创建一个新的搜索/分析任务
        :param request: 用户的请求对象
        :return: 任务 ID (task_id)
        """
        task_id = str(uuid.uuid4())
        # 记录任务初始状态为 "submitted"
        self.tasks[task_id] = {
            "request": request,
            "status": "submitted",
            "created_at": str(asyncio.get_event_loop().time()),
            "result": None
        }
        return task_id

    async def refine_intel_item(self, item_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use RefinementAgent to clean, translate, and tag a single intel item.
        Returns a dict with updated fields (title, summary, tags).
        If fails, returns None or original dict.
        """
        if not self.agentscope_inited or not self.refinement_agent:
            print("Orchestrator: AgentScope not inited, skipping refinement.")
            return item_dict

        try:
            # Construct Input Prompt
            original_text = item_dict.get("original", "")
            # Truncate original text to avoid token overflow (e.g. 2000 chars)
            if len(original_text) > 2000:
                original_text = original_text[:2000] + "...(truncated)"
                
            input_text = f"""
            Title: {item_dict.get('title')}
            Summary: {item_dict.get('summary')}
            Original Text Snippet: {original_text}
            """
            
            # Call Agent
            msg = Msg(name="User", content=input_text, role="user")
            response_msg = await self.refinement_agent.reply(msg)
            
            # Extract JSON
            refined_data = extract_json_from_text(response_msg.content)
            
            if refined_data:
                # Merge into original item
                # Only update fields that exist in refined_data
                if "title" in refined_data:
                    item_dict["title"] = refined_data["title"]
                if "summary" in refined_data:
                    item_dict["summary"] = refined_data["summary"]
                if "tags" in refined_data:
                    # refined_data["tags"] should be a list of dicts {"label": "x", "color": "y"}
                    # We need to ensure it matches what frontend expects or backend model expects.
                    # Backend model (IntelItem) expects List[Tag] object, but here we are working with dicts 
                    # before Pydantic validation. So list of dicts is perfect.
                    item_dict["tags"] = refined_data["tags"]
                    
                print(f"Orchestrator: Item {item_dict.get('id')} refined successfully.")
                return item_dict
            else:
                print(f"Orchestrator: Failed to extract JSON from refinement response. Keeping original.")
                return item_dict
                
        except Exception as e:
            print(f"Orchestrator: Error during refinement: {e}")
            return item_dict

    async def run_stream(self, task_id: str) -> AsyncGenerator[str, None]:
        """
        异步执行任务并以 SSE (Server-Sent Events) 格式流式返回进度和结果
        :param task_id: 任务 ID
        """
        # 检查任务是否存在
        if task_id not in self.tasks:
            yield f"event: error\ndata: Task not found\n\n"
            return

        task = self.tasks[task_id]
        task["status"] = "running"
        req: AgentSearchRequest = task["request"]

        # 1. 发送开始状态
        yield f"event: status\ndata: {json.dumps({'status': 'running'})}\n\n"

        # 如果 AgentScope 已初始化，尝试使用真实智能体进行处理
        if self.agentscope_inited:
            try:
                # 发送初始化进度
                yield f"event: progress\ndata: {json.dumps({'step': 'init', 'message': 'Initializing AgentScope Analyst...'})}\n\n"
                
                # RAG (检索增强生成) 步骤: 从数据库检索相关情报
                db = SessionLocal()
                try:
                    items, _ = crud.get_filtered_intel(
                        db,
                        type_filter=req.type or "all",
                        q=req.query,
                        limit=5
                    )
                finally:
                    db.close()
                
                # 读取外部上下文文件 (data.txt) 如果存在
                data_txt_content = ""
                data_txt_path = "/home/system_/system_mvp/data.txt"
                try:
                    if os.path.exists(data_txt_path):
                        with open(data_txt_path, "r", encoding="utf-8") as f:
                            data_txt_content = f.read()
                except Exception as e:
                    print(f"Error reading data.txt: {e}")

                # 构建上下文文本，包含检索到的情报摘要
                context_text = "\\n".join([f"- {item.title}: {item.summary}" for item in items])
                
                # 如果有外部文件内容，也添加到上下文中
                if data_txt_content:
                    context_text += f"\\n\\nAdditional Context from File (data.txt):\\n{data_txt_content}"
                
                # 准备发送给 Agent 的消息
                user_content = f"Context:\n{context_text}\n\nQuery: {req.query}"
                msg = Msg(name="User", content=user_content, role="user")
                
                # 发送分析中进度
                yield f"event: progress\ndata: {json.dumps({'step': 'analysis', 'message': 'Agent is analyzing data (LLM)...'})}\n\n"
                
                # 调用 Agent 进行回复 (异步调用)
                # self.analyst_agent.reply 会调用 LLM 并返回分析结果
                response_msg = await self.analyst_agent.reply(msg)
                
                answer = response_msg.content
                
                # 构造最终结果对象
                result = AgentSearchResponse(items=items, answer=answer)
                task["status"] = "done"
                task["result"] = result

                # 发送最终结果和完成状态
                yield f"event: result\ndata: {result.model_dump_json()}\n\n"
                yield f"event: status\ndata: {json.dumps({'status': 'done'})}\n\n"
                return

            except Exception as e:
                # 如果 Agent 执行出错，打印堆栈并回退到模拟逻辑
                print(f"AgentScope Execution Error: {e}")
                import traceback
                traceback.print_exc()
                yield f"event: progress\ndata: {json.dumps({'step': 'error', 'message': f'Agent error: {str(e)}. Falling back to simulation.'})}\n\n"
                # Fall through to mock logic (继续执行下方的模拟逻辑)

        # 2. 回退/模拟仿真逻辑 (当 AgentScope 未初始化或出错时执行)
        steps = [
            {"name": "retrieve", "desc": "Retrieving relevant intel..."},
            {"name": "rerank", "desc": "Scoring and reranking items..."},
            {"name": "summarize", "desc": "Generating summaries..."},
            {"name": "tagging", "desc": "Auto-tagging content..."},
            {"name": "compose_answer", "desc": "Composing final answer..."}
        ]

        # 模拟各个步骤的耗时
        for step in steps:
            await asyncio.sleep(0.8) # Simulate work
            yield f"event: progress\ndata: {json.dumps({'step': step['name'], 'message': step['desc']})}\n\n"

        # 3. 执行模拟"搜索" (仅数据库查询)
        db = SessionLocal()
        try:
            items, _ = crud.get_filtered_intel(
                db,
                type_filter=req.type or "all",
                q=req.query,
                range_filter=req.range or "all",
                limit=req.top_k
            )
        finally:
            db.close()

        # 生成模拟回答
        answer = f"Based on the analysis of {len(items)} items, the situation regarding '{req.query}' shows significant activity. Key trends include recent diplomatic moves and economic indicators."
        
        result = AgentSearchResponse(items=items, answer=answer)
        
        task["status"] = "done"
        task["result"] = result

        # 4. 发送模拟结果
        yield f"event: result\ndata: {result.model_dump_json()}\n\n"
        yield f"event: status\ndata: {json.dumps({'status': 'done'})}\n\n"

    def get_task_status(self, task_id: str):
        """获取任务当前状态"""
        return self.tasks.get(task_id)

    async def analyze_data_file(self):
        """
        后台任务：分析数据文件
        流程：
        1. 将 data.txt 的内容摄入到数据库 (RawData 表)
        2. 读取未处理的 RawData
        3. 使用 ExtractorAgent 提取情报 (标题、摘要、标签等)
        4. 将提取出的结构化情报存入 IntelItem 表
        """
        db = SessionLocal()
        try:
            # 1. 摄入 data.txt 文件
            data_path = "/home/system_/system_mvp/data.txt"
            if os.path.exists(data_path):
                try:
                    with open(data_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    if content.strip():
                        print("Ingesting data.txt into database...")
                        # 创建原始数据记录
                        crud.create_raw_data(db, content, source="data.txt")
                        # 重命名文件为 .bak 防止重复处理
                        os.rename(data_path, data_path + ".bak")
                except Exception as e:
                    print(f"Error ingesting data.txt: {e}")

            # 2. 获取待处理数据
            pending_items = crud.get_unprocessed_raw_data(db, limit=1) # 暂时每次只处理1条
            if not pending_items:
                print("No pending raw data to process.")
                return

            if not self.agentscope_inited:
                print("AgentScope not initialized, skipping analysis.")
                return

            print(f"Processing {len(pending_items)} raw data items...")
            
            from app.models import IntelItem, Tag
            from datetime import datetime
            
            for raw_item in pending_items:
                content = raw_item.content
                # 构造 Prompt 消息，截取前 15000 字符防止 Token 溢出
                msg = Msg(name="User", content=f"Raw Text:\n{content[:15000]}", role="user")
                
                try:
                    print("Starting model invocation via Agent...")
                    # 调用 ExtractorAgent 进行提取
                    response_msg = await self.extractor_agent.reply(msg)
                    
                    resp_content = response_msg.content
                    print(f"Agent analysis result: {resp_content[:100]}...")

                    try:
                        items_data = extract_json_from_text(resp_content)
                    except json.JSONDecodeError as e:
                        print(f"JSON Parse Error: {e}. Content: {resp_content[:200]}")
                        continue # 跳过当前条目
                    except Exception as e:
                        print(f"Error parsing JSON: {e}")
                        continue

                    # 遍历提取出的条目并保存到数据库
                    for item in items_data:
                        # 创建标签对象
                        tags = []
                        for t in item.get("tags", []):
                            # 判断是否为国家标签，如果是则设置为红色
                            color = "blue"
                            # 简单的国家列表匹配逻辑
                            countries = [
                                '中国', '美国', '日本', '韩国', '俄罗斯', '英国', '法国', '德国', '印度', 
                                '加拿大', '澳大利亚', '巴西', '朝鲜', '伊朗', '以色列', '乌克兰', '欧盟', 
                                '东盟', '意大利', '西班牙', '荷兰', '瑞士', '瑞典', '新加坡', '越南'
                            ]
                            if any(country in t for country in countries):
                                color = "red"
                            
                            tags.append(Tag(label=t, color=color))
                        
                        # 解析日期
                        try:
                            item_time = datetime.strptime(item.get("date"), "%Y-%m-%d")
                        except:
                            item_time = datetime.now()
                            
                        # 创建 IntelItem 对象
                        intel_item = IntelItem(
                            id=str(uuid.uuid4()),
                            title=item.get("title", "Untitled"),
                            summary=item.get("summary", ""),
                            source=item.get("source", "Unknown"),
                            time=item_time.strftime("%Y/%m/%d %H:%M"),
                            timestamp=item_time.timestamp(),
                            tags=tags,
                            favorited=False,
                            is_hot=item.get("is_hot", False)
                        )
                        
                        # 保存到数据库
                        crud.create_intel_item(db, intel_item)
                        
                    print(f"Successfully processed raw item {raw_item.id} and added {len(items_data)} intel items.")
                    # 标记原始数据为已处理
                    crud.mark_raw_data_processed(db, raw_item.id)
                    
                except Exception as e:
                    print(f"Failed to analyze raw item {raw_item.id}: {e}")
                    import traceback
                    traceback.print_exc()

        finally:
            db.close()

# 创建全局单例实例
orchestrator = AgentOrchestrator()
