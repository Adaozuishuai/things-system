# 项目审查报告：AI 原生情报分析平台 (AI-Native Intelligence Analysis Platform)

## 1. 系统概述 (System Overview)
本项目是一个**AI 驱动的实时情报采集与分析平台**。系统从外部数据源（如 Payload CMS）采集情报，通过 SSE 将“热流”推送给前端；同时将“历史/搜索”能力建立在数据库与 Agent（LLM）辅助检索分析之上。

在前端交互层面，“热点”分成两种使用方式：
*   **热点流 (Hot Stream)**：不依赖搜索词，持续接收后端 SSE 推送的最新热点。
*   **热点搜索模式 (Hot Search Mode)**：输入搜索词后，搜索结果由“实时 SSE 缓存 + 数据库查询”两路合并、去重、按时间排序，确保**未落库但已通过 SSE 收到的热点**也能被检索到，并且新到达的 SSE 事件会实时刷新结果集。

**核心价值**: 将实时热流与可追溯历史结合，提供自动化、实时化、可视化的情报作业流程。

---

## 2. 技术栈 (Tech Stack)

### 后端 (Backend)
*   **Framework**: FastAPI (Python 3.9+) - 高性能异步 Web 框架。
*   **AI Framework**: AgentScope - 阿里开源的多智能体协同框架，负责 Agent 编排。
*   **LLM Provider**: DashScope (Aliyun Qwen-Max) - 提供通义千问大模型能力。
*   **Database**: SQLite (SQLAlchemy ORM) - 轻量级关系型数据库，便于部署与迁移 (可无缝切换至 PostgreSQL)。
*   **Auth**: OAuth2 + JWT + BCrypt - 标准的安全认证与密码加密体系。
*   **Concurrency**: Asyncio + Aiohttp - 高并发网络请求处理。
*   **Real-time**: Server-Sent Events (SSE) - 实现服务器向前端的单向实时数据推送。

### 前端 (Frontend)
*   **Framework**: React 18 + Vite - 现代化的前端开发体验与构建速度。
*   **Language**: TypeScript - 强类型约束，提升代码健壮性。
*   **Styling**: Tailwind CSS - 原子化 CSS，支持深色模式 (Dark Mode)。
*   **State Management**: React Context API - 管理全局认证与用户状态。
*   **UI Components**: React Virtuoso (虚拟列表) + Lucide React (图标库)。
*   **Routing**: React Router v6 - 页面路由管理。

---

## 3. 核心架构与功能模块 (Architecture & Modules)

### 3.1 用户与认证层 (User & Auth Layer)
负责系统的安全准入与个性化管理。
*   **[auth.py](file:///home/system_/system_mvp/backend/app/routes/auth.py)**: 处理注册、登录、Token 刷新。
*   **[auth_utils.py](file:///home/system_/system_mvp/backend/app/services/auth_utils.py)**: 封装密码哈希 (Bcrypt) 与 JWT 编解码逻辑。
*   **[AuthContext.tsx](file:///home/system_/system_mvp/frontend/src/context/AuthContext.tsx)**: 前端状态机，管理用户登录态持久化。

### 3.2 数据采集层 (Ingestion Layer)
负责从外部源高效获取数据。
*   **[payload_poller.py](file:///home/system_/system_mvp/backend/app/services/payload_poller.py)**: 核心采集引擎。
    *   **自动登录**: 模拟用户行为获取 CMS Token。
    *   **增量采集**: 维护 `last_fetched_ids` 集合，防止数据重复。
    *   **数据清理**: 定时清理 30 天前旧数据，保持数据库轻量。
    *   **热流广播**: 当前路径以“直通映射”为主（不启用 LLM 精炼），将新条目广播到全局 SSE；并将 `regional_country/domain/topicType` 等字段映射为标签。

### 3.3 智能处理层 (Processing Layer)
系统的“大脑”，负责数据价值提升。
*   **[orchestrator.py](file:///home/system_/system_mvp/backend/app/agent/orchestrator.py)**: 任务调度器，协调数据流入 Agent。
*   **[agents.py](file:///home/system_/system_mvp/backend/app/agent/agents.py)**: 定义具体的 Agent 行为。
    *   **AnalystAgent**: 为“历史/搜索”提供 LLM 辅助分析（基于数据库或热流缓存检索到的上下文）。
    *   **DataExtractorAgent**: 支持离线/批处理（`data.txt` -> `raw_data` -> 抽取结构化情报 -> 入库）。
    *   **RefinementAgent**: 提供单条情报精炼能力（已实现，但当前未启用在 CMS 轮询的热流路径中）。
    *   **容错机制**: 当 AgentScope/LLM 不可用或执行失败时，会回退到模拟逻辑，保证接口可用性。
    *   **结构化输出**: 对抽取/精炼场景做了 JSON 提取与兼容性修复，降低模型输出不稳定带来的失败率。

### 3.4 存储与接口层 (Storage & API Layer)
负责数据持久化与对外服务。
*   **[crud.py](file:///home/system_/system_mvp/backend/app/crud.py)**: 统一的数据库操作入口 (Create, Read, Update, Delete)。
*   **[db_models.py](file:///home/system_/system_mvp/backend/app/db_models.py)**: 定义 `IntelItem`, `User`, `RawData` 等数据表结构。
*   **[intel.py](file:///home/system_/system_mvp/backend/app/routes/intel.py)**: 提供情报查询、详情、收藏、导出等 RESTful 接口。
    *   列表检索：`GET /intel/?type=hot|history|all&q=...&range=...`，热点搜索模式会用它拉取“已落库热点”作为数据库侧结果集。
    *   详情：`GET /intel/{id}` 优先读库；未落库则从编排器热流缓存取回并写入数据库（保证详情可追溯）。
    *   收藏：`POST /intel/{id}/favorite` 优先更新数据库；未落库则从热流缓存构造条目并入库后再更新收藏。
    *   导出：`POST /intel/export` 支持按 ID 列表导出；缺失条目会尝试从热流缓存补齐并入库后导出。
*   **[agent.py](file:///home/system_/system_mvp/backend/app/routes/agent.py)**: 提供 Agent 任务创建与 SSE 流式结果（含全局热流 SSE：`GET /agent/stream/global`）。

### 3.5 前端展示层 (Presentation Layer)
负责数据的可视化呈现与交互。
*   **[IntelList.tsx](file:///home/system_/system_mvp/frontend/src/components/intel/IntelList.tsx)**: 核心组件，支持大数据量虚拟滚动与实时更新动画。
*   **[useGlobalIntel.ts](file:///home/system_/system_mvp/frontend/src/hooks/useGlobalIntel.ts)**: 自定义 Hook，封装 SSE 连接逻辑，实现数据实时同步。
    *   连接端点：`GET /agent/stream/global`（通过 [api.ts](file:///home/system_/system_mvp/frontend/src/api.ts) 的 `getGlobalStreamUrl` 生成 URL）。
    *   初始同步：接收 `initial_batch` 事件，将服务端 `global_cache` 的最近消息合并进列表。
    *   增量更新：接收 `new_intel` 事件，将最新条目合并进列表（按 `timestamp` 倒序）。
    *   断线续传：使用 `after_ts/after_id` 作为游标重连，避免重复推送。
*   **[IntelPage.tsx](file:///home/system_/system_mvp/frontend/src/pages/IntelPage.tsx)**: 情报主页面，包含“热点流 / 热点搜索模式 / 历史搜索”三种主路径。
    *   热点流：`type === 'hot'` 且无搜索词时，直接展示 `useGlobalIntel(true)` 的实时列表。
    *   热点搜索模式：`type === 'hot'` 且 `hotSearchQuery` 非空时启用。
        *   数据来源 A（数据库）：调用 `getIntel('hot', hotSearchQuery, range, ...)` 拉取已落库热点命中项。
        *   数据来源 B（实时缓存）：对 `useGlobalIntel` 的 `liveItems` 做 `matchesHotSearch` 过滤。
        *   合并策略：用 `Map(id -> item)` 去重，实时缓存条目会覆盖同 ID 的数据库条目，再按 `timestamp` 倒序排序。
        *   推送提示：连接状态条在热点搜索模式下展示“正在推送{搜索词}有关消息”。
*   **[SettingsPage.tsx](file:///home/system_/system_mvp/frontend/src/pages/SettingsPage.tsx)**: 用户个人中心，支持资料修改与偏好设置。

---

## 4. 项目文件结构 (File Structure)

```
system_mvp/
├── backend/
│   ├── app/
│   │   ├── agent/          # AI 智能体逻辑 (Orchestrator, Refiner)
│   │   ├── routes/         # API 路由 (Auth, Intel, Agent)
│   │   ├── services/       # 业务服务 (Pollers, Auth Utils)
│   │   ├── crud.py         # 数据库 CRUD 操作
│   │   ├── models.py       # Pydantic 数据模型 (Schema)
│   │   ├── db_models.py    # SQLAlchemy 数据库模型 (Table)
│   │   ├── database.py     # 数据库连接配置
│   │   └── main.py         # FastAPI 应用入口
│   ├── check_latest_db.py   # 辅助脚本：查看最新入库情报
│   ├── requirements.txt    # Python 依赖
│   └── intel.db            # SQLite 数据库文件
├── frontend/
│   ├── src/
│   │   ├── components/     # UI 组件 (IntelItem, IntelList, Toolbar, Layout, Sidebar)
│   │   ├── pages/          # 页面组件 (IntelPage, IntelDetail, Favorites, Login, Register, Settings)
│   │   ├── context/        # React Context (AuthContext)
│   │   ├── hooks/          # 自定义 Hooks (useGlobalIntel)
│   │   ├── api.ts          # Axios API 客户端
│   │   └── App.tsx         # 根组件与路由配置
│   ├── package.json        # Node 依赖
│   └── vite.config.ts      # Vite 配置
├── tests/                  # 自动化测试套件 (pytest)
└── readme.md               # 项目说明文档
```

---

## 5. 运行状态与测试 (Status & Testing)

### 运行状态
*   ✅ **用户系统**: 注册、登录、个人资料管理功能完备。
*   ✅ **数据流转**: 从 Payload CMS 采集 -> 热流 SSE 推送（支持热点搜索：缓存+数据库合并检索）-> 详情/收藏/导出按需落库 -> 历史检索。
*   ✅ **Agent 能力**: 历史/搜索提供 LLM 辅助回答；离线抽取链路支持 `data.txt` 批处理入库。
*   ✅ **界面交互**: 支持深色模式，响应式布局，操作流畅。

### 自动化测试
项目测试用例位于 `tests/` 目录下，形态混合：
*   **本地服务集成测试**（需要先启动后端）：例如 `test_auth_flow.py`、`test_settings_flow.py`。
*   **进程内单元/组件测试**（直接实例化模块）：例如 `test_sse_resume.py`（验证 SSE 断线续传与 initial_batch 过滤）、`test_hot_intel_search.py`（验证热点检索逻辑）、`test_toggle_favorite_hot_cache.py`（验证未落库条目的收藏落库路径）。

---

## 6. 审查结论与改进清单 (Review Findings)

1.  **文档与现状一致性**: 当前运行态以“热流直通广播 + 详情/收藏/导出按需落库”为主；热点搜索模式已实现“实时缓存 + 数据库”合并检索。LLM 精炼能力存在但未接入 CMS 轮询路径，应持续保持文档与实现同步（本次已修正关键描述）。
2.  **热流可靠性边界**: `global_cache` 为内存态（固定长度队列），服务重启后会丢失，热点流与热点搜索模式的“实时侧可检索窗口”会重置。可考虑将游标/缓存持久化（SQLite/Redis）或依赖上游排序游标增量拉取。
3.  **落库策略清晰**: 按需落库降低了写入压力，但也意味着历史库覆盖依赖用户行为与导出/收藏行为；若需要完整留存，应提供后台入库开关或定时落库策略。
4.  **LLM 调用降级**: `AgentScope` 初始化失败与执行错误会回退到模拟逻辑，保证接口可用；面向生产建议在前端显式区分“真实模型输出”与“降级输出”。
5.  **测试形态**: 已同时存在集成测试与进程内测试；建议为 CI 场景拆分“需后端启动”与“纯单测”两类测试，并补充静态检查（lint/typecheck）。

---

## 7. 后续优化建议 (Future Improvements)

1.  **数据库迁移**: 生产环境建议迁移至 PostgreSQL 以获得更好的并发性能和 JSON 查询能力。
2.  **向量检索**: 引入向量数据库 (如 Milvus/Chroma)，实现基于语义的情报搜索 (RAG)。
3.  **多模态支持**: 扩展 Agent 能力，支持图片、PDF 等多模态数据的解析与提炼。
4.  **部署容器化**: 编写 Dockerfile 和 Docker Compose 配置，简化部署流程。
