# 项目审查报告：AI 原生情报分析平台 (AI-Native Intelligence Analysis Platform)

## 1. 系统概述 (System Overview)
本项目是一个**AI 驱动的实时情报采集与分析平台**。系统从外部数据源（如 Payload CMS）采集情报，通过 SSE 将“热流”推送给前端；同时将“历史/搜索”能力建立在数据库与 Agent（LLM）辅助检索分析之上。

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
*   **[intel.py](file:///home/system_/system_mvp/backend/app/routes/intel.py)**: 提供情报查询、筛选、收藏等 RESTful 接口；详情接口支持“从热流缓存落库”（点击详情时持久化）。
*   **[agent.py](file:///home/system_/system_mvp/backend/app/routes/agent.py)**: 提供 Agent 任务创建与 SSE 流式结果（含全局热流 SSE）。

### 3.5 前端展示层 (Presentation Layer)
负责数据的可视化呈现与交互。
*   **[IntelList.tsx](file:///home/system_/system_mvp/frontend/src/components/intel/IntelList.tsx)**: 核心组件，支持大数据量虚拟滚动与实时更新动画。
*   **[useGlobalIntel.ts](file:///home/system_/system_mvp/frontend/src/hooks/useGlobalIntel.ts)**: 自定义 Hook，封装 SSE 连接逻辑，实现数据实时同步。
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
│   ├── tests/              # 自动化测试套件
│   ├── check_latest_db.py   # 辅助脚本：查看最新入库情报
│   ├── requirements.txt    # Python 依赖
│   └── intel.db            # SQLite 数据库文件
├── frontend/
│   ├── src/
│   │   ├── components/     # UI 组件 (IntelItem, Banner, Sidebar)
│   │   ├── pages/          # 页面组件 (Login, IntelPage, Settings)
│   │   ├── context/        # React Context (AuthContext)
│   │   ├── hooks/          # 自定义 Hooks (useGlobalIntel)
│   │   ├── api.ts          # Axios API 客户端
│   │   └── App.tsx         # 根组件与路由配置
│   ├── package.json        # Node 依赖
│   └── vite.config.ts      # Vite 配置
└── readme.md               # 项目说明文档
```

---

## 5. 运行状态与测试 (Status & Testing)

### 运行状态
*   ✅ **用户系统**: 注册、登录、个人资料管理功能完备。
*   ✅ **数据流转**: 从 Payload CMS 采集 -> 热流 SSE 推送 ->（详情页）缓存落库 -> 历史检索/收藏。
*   ✅ **Agent 能力**: 历史/搜索提供 LLM 辅助回答；离线抽取链路支持 `data.txt` 批处理入库。
*   ✅ **界面交互**: 支持深色模式，响应式布局，操作流畅。

### 自动化测试
项目包含完善的测试用例，位于 `backend/tests/` 目录下：
*   目前以“脚本型集成测试”为主（通过 `requests` 访问本地服务端点），适合回归关键业务流程。
*   `test_full_pipeline.py`: 验证精炼/映射链路关键字段不丢失。
*   `test_auth_flow.py`: 验证用户认证流程。
*   `test_settings_flow.py`: 验证用户设置更新逻辑。

---

## 6. 审查结论与改进清单 (Review Findings)

1.  **文档与现状一致性**: 当前运行态以“热流直通广播 + 详情页落库”为主；LLM 精炼能力存在但未接入 CMS 轮询路径。建议持续保持文档与实现同步（本次已修正关键描述）。
2.  **热流可靠性边界**: `last_fetched_ids` 与 `global_cache` 均为内存态，服务重启后会丢失，可能导致热流重复、热流历史无法追溯。可考虑将去重游标/缓存做持久化（SQLite/Redis）或以 CMS 侧排序游标增量拉取。
3.  **落库策略清晰**: 详情页“缓存落库”设计降低了数据库写入压力，但也意味着历史库覆盖依赖用户访问行为；若需要完整留存，应提供后台入库开关或定时落库策略。
4.  **LLM 调用降级**: `AgentScope` 初始化失败与执行错误均能回退到模拟逻辑，保证接口可用；若面向生产，建议区分“不可用”与“模拟结果”在前端提示层面的语义。
5.  **测试形态**: 后端测试以集成脚本为主，覆盖业务路径但对 CI 友好度较弱；建议逐步补充可直接运行的单元测试（pytest）与静态检查（lint/typecheck）。

---

## 7. 后续优化建议 (Future Improvements)

1.  **数据库迁移**: 生产环境建议迁移至 PostgreSQL 以获得更好的并发性能和 JSON 查询能力。
2.  **向量检索**: 引入向量数据库 (如 Milvus/Chroma)，实现基于语义的情报搜索 (RAG)。
3.  **多模态支持**: 扩展 Agent 能力，支持图片、PDF 等多模态数据的解析与提炼。
4.  **部署容器化**: 编写 Dockerfile 和 Docker Compose 配置，简化部署流程。
