# 项目审查报告：AI 原生情报分析平台 (AI-Native Intelligence Analysis Platform)

## 1. 系统概述 (System Overview)
本项目是一个**AI 驱动的实时情报采集与分析平台**。系统自动从外部数据源（如 Payload CMS）采集原始情报，利用 LLM（大语言模型）进行智能提炼（去噪、翻译、摘要、自动打标），并通过实时通道（SSE）将高价值情报推送给前端大屏展示。

**核心价值**: 从海量杂乱信息中提取关键情报，实现自动化、实时化、可视化的情报作业流程。

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
    *   **并发控制**: 引入 `asyncio.Semaphore` 限制 LLM 并发请求数，防止 API 限流或系统过载。
    *   **数据清洗**: 自动清理 30 天前的旧数据，保持数据库轻量。

### 3.3 智能处理层 (Processing Layer)
系统的“大脑”，负责数据价值提升。
*   **[orchestrator.py](file:///home/system_/system_mvp/backend/app/agent/orchestrator.py)**: 任务调度器，协调数据流入 Agent。
*   **[agents.py](file:///home/system_/system_mvp/backend/app/agent/agents.py)**: 定义具体的 Agent 行为。
    *   **RefinementAgent**: 执行清洗、翻译、摘要、打标任务。
    *   **容错机制**: 当 LLM 调用失败时，自动回退到 Mock 逻辑，确保业务连续性。
    *   **结构化输出**: 强制 LLM 返回 JSON 格式，并进行鲁棒性解析。

### 3.4 存储与接口层 (Storage & API Layer)
负责数据持久化与对外服务。
*   **[crud.py](file:///home/system_/system_mvp/backend/app/crud.py)**: 统一的数据库操作入口 (Create, Read, Update, Delete)。
*   **[db_models.py](file:///home/system_/system_mvp/backend/app/db_models.py)**: 定义 `IntelItem`, `User`, `RawData` 等数据表结构。
*   **[intel.py](file:///home/system_/system_mvp/backend/app/routes/intel.py)**: 提供情报查询、筛选、收藏等 RESTful 接口，以及 SSE 推送端点。

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
└── README.md               # 项目说明文档
```

---

## 5. 运行状态与测试 (Status & Testing)

### 运行状态
*   ✅ **用户系统**: 注册、登录、个人资料管理功能完备。
*   ✅ **数据流转**: 从 Payload CMS 采集 -> AI 提炼 -> 数据库存储 -> 前端实时推送的全链路已打通。
*   ✅ **并发优化**: 采集器已通过信号量 (Semaphore) 解决了并发无限增长的问题。
*   ✅ **界面交互**: 支持深色模式，响应式布局，操作流畅。

### 自动化测试
项目包含完善的测试用例，位于 `backend/tests/` 目录下：
*   `test_full_pipeline.py`: 验证全链路数据处理逻辑。
*   `test_auth_flow.py`: 验证用户认证流程安全性。
*   `test_settings_flow.py`: 验证用户设置更新逻辑。

---

## 6. 后续优化建议 (Future Improvements)

1.  **数据库迁移**: 生产环境建议迁移至 PostgreSQL 以获得更好的并发性能和 JSON 查询能力。
2.  **向量检索**: 引入向量数据库 (如 Milvus/Chroma)，实现基于语义的情报搜索 (RAG)。
3.  **多模态支持**: 扩展 Agent 能力，支持图片、PDF 等多模态数据的解析与提炼。
4.  **部署容器化**: 编写 Dockerfile 和 Docker Compose 配置，简化部署流程。
