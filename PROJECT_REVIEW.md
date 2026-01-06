# Project Review: AI-Native Intelligence Analysis Platform

## 1. 系统概述 (System Overview)
本项目是一个**AI 驱动的实时情报采集与分析平台**。系统自动从外部数据源（Payload CMS）采集情报，利用 LLM（Large Language Model）进行智能提炼（去噪、翻译、摘要、打标），并通过实时通道（SSE）推送给前端大屏展示。

---

## 2. 技术栈 (Tech Stack)

### 后端 (Backend)
*   **Framework**: FastAPI (Python) - 高性能异步 Web 框架。
*   **AI Framework**: AgentScope (Multi-Agent Orchestration) - 阿里开源的多智能体协同框架。
*   **LLM Provider**: DashScope (Aliyun Qwen-Max) - 提供顶级中文处理能力的通义千问模型。
*   **Database**: PostgreSQL - 存储结构化情报数据。
*   **Concurrency**: Asyncio + Aiohttp - 异步并发处理网络请求。
*   **Real-time**: Server-Sent Events (SSE) - 服务器向前端单向实时推送。

### 前端 (Frontend)
*   **Framework**: React 18 + Vite - 现代前端 UI 框架与构建工具。
*   **Styling**: Tailwind CSS - 原子化样式框架。
*   **Language**: TypeScript - 强类型脚本语言。
*   **State Management**: React Hooks (Custom SSE Hooks) - 实时数据流状态管理。

---

## 3. 核心架构与详细功能清单 (Architecture & Functionality)

### 3.1 数据采集层 (Ingestion Layer)
*   **[payload_poller.py](file:///home/system_/system_mvp/backend/app/services/payload_poller.py)**: **全自动数据引擎**
    *   `_login()`: 模拟用户登录 Payload CMS，获取 JWT Token 以通过 API 鉴权。
    *   `_poll_step()`: 核心循环。执行“登录 -> 拉取数据 -> 处理数据”的单次任务。
    *   `_process_data()`: **数据流水线控制中心**。
        1.  **去重**: 检查 ID 是否在 `last_fetched_ids` 或数据库中，防止重复入库。
        2.  **触发提炼**: 调用 Orchestrator 进行 AI 加工。
        3.  **模型转换**: 将原始 JSON 转换为标准的 `IntelItem` 模型。
        4.  **持久化**: 调用 CRUD 存入 PostgreSQL。
        5.  **实时广播**: 通过 SSE 连接池将新数据瞬间推送到所有在线前端。

### 3.2 智能处理层 (Processing Layer)
*   **[agents.py](file:///home/system_/system_mvp/backend/app/agent/agents.py)**: **AI 智能体核心实现**
    *   `DataExtractorAgent`: 封装了 AgentScope 的底层调用。
        *   **流式解析 (Stream Parsing)**: 特别修复了针对 DashScope 全量更新流的解析逻辑，能够从持续增长的字符流中提取最终的 JSON。
        *   **Robust Parsing**: 兼容多种模型返回格式（ModelResponse, dict, ChatResponse）。
    *   `RefinementAgent`: **情报分析专家**。
        *   **智能加工**: 根据预设 Prompt 进行去噪、翻译、摘要重写。
        *   **颜色标签系统**: 自动为“国家/地区”打上红色标签，为“领域”打上蓝色标签。
        *   **Mock Fallback (容错机制)**: **关键功能**。当 LLM 报错（如 API Key 失效或解析失败）时，自动触发回退逻辑，通过规则保留原始标题摘要，保证业务不中断。
*   **[orchestrator.py](file:///home/system_/system_mvp/backend/app/agent/orchestrator.py)**: **调度协调器**
    *   `AgentOrchestrator`: 单例管理 Agent 的初始化、模型配置（DASHSCOPE_API_KEY）以及任务分发。

### 3.3 存储与接口层 (Data & API Layer)
*   **[db_models.py](file:///home/system_/system_mvp/backend/app/db_models.py)**: **ORM 模型**
    *   定义了 `intel_items` 表。使用 `JSONB` 存储 tags，支持高效的情报检索。
*   **[intel.py](file:///home/system_/system_mvp/backend/app/routes/intel.py)**: **情报路由**
    *   `GET /events`: 保持 SSE 长连接，实现零延迟数据推送。
    *   `GET /`: 提供分页查询，供前端加载历史数据。

### 3.4 前端展示层 (Presentation Layer)
*   **[useGlobalIntel.ts](file:///home/system_/system_mvp/frontend/src/hooks/useGlobalIntel.ts)**: **实时数据同步钩子**
    *   封装了 `EventSource` 连接逻辑。自动监听后端 `new_intel` 事件并实时更新 UI 状态。
*   **[IntelList.tsx](file:///home/system_/system_mvp/frontend/src/components/intel/IntelList.tsx)**: **动态列表组件**
    *   实现数据项的平滑插入动画。支持大批量数据的实时渲染。
*   **[IntelItem.tsx](file:///home/system_/system_mvp/frontend/src/components/intel/IntelItem.tsx)**: **情报交互卡片**
    *   **标签渲染**: 根据后端分配的颜色动态渲染红色/蓝色/灰色标签。
    *   **交互逻辑**: 支持详情跳转、收藏状态切换。

---

## 4. 自动化测试验证 (Testing & Verification)

| 测试文件 | 验证功能 |
| :--- | :--- |
| `tests/test_agent_llm.py` | 验证 `RefinementAgent` 是否能成功调用 LLM 并正确解析返回的消息对象。 |
| `tests/test_real_api_ingestion.py` | **全链路集成测试**。验证：真实 CMS 登录 -> 抓取 -> AI 提炼 -> 数据库存入 -> 数据库查询校验。 |
| `tests/test_full_pipeline.py` | 验证数据从 Orchestrator 处理后到 Pydantic 模型校验及入库的逻辑完整性。 |

---

## 5. 运行状态 (System Status)
*   **AI 提炼**: ✅ **完全开启**。支持流式处理和 JSON 自动纠错。
*   **数据流**: ✅ **实时连通**。CMS -> Backend -> Frontend 全链路延迟 < 1s (推送阶段)。
*   **容错性**: ✅ **高**。具备 API 异常自动降级能力。
*   **环境配置**: ✅ 已通过 `.env` 注入真实 CMS 凭据与 DashScope API Key。
