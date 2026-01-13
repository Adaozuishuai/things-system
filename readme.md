# Intel Agent MVP

An intelligent intelligence aggregation and refinement platform. This system polls data from various sources (CMS, APIs), refines it using AI agents, and presents it in a modern, interactive dashboard.

## 🚀 Features

-   **Multi-Source Polling**: Automatically fetches data from Payload CMS and other API sources.
-   **AI Refinement**: Uses AgentScope and LLMs (DashScope) to analyze, summarize, and tag intelligence items.
-   **Real-time Updates**: Live data streaming and updates via server-side events (SSE).
-   **Intelligence Dashboard**:
    -   Virtualized scrolling for high performance with large datasets.
    -   Advanced filtering (Time range, Hot topics, Search).
    -   Detail view with original vs. refined content.
-   **User Management**:
    -   Secure Authentication (JWT).
    -   Profile management and preferences.
    -   Favorites system.
-   **Data Export**: Support for exporting intelligence reports in CSV, JSON, and DOCX formats.

## 🛠️ Tech Stack

### Backend
-   **Framework**: Python (FastAPI)
-   **Database**: SQLite (SQLAlchemy ORM)
-   **AI/LLM**: AgentScope, DashScope
-   **Async**: asyncio, aiohttp
-   **Auth**: OAuth2 with JWT (Passlib, Python-Jose)

### Frontend
-   **Framework**: React 18 (Vite)
-   **Language**: TypeScript
-   **Styling**: Tailwind CSS
-   **UI Components**: Lucide React, React Virtuoso (Virtual List)
-   **State/API**: Context API, Axios

## ✅ Prerequisites

-   Python 3.9+
-   Node.js 16+
-   DashScope API Key (for AI features)
-   Payload CMS credentials (optional, for CMS integration)

## ⚡ Getting Started

### 1. Backend Setup

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```

2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r ../requirements.txt
    ```

4.  Configure Environment Variables:
    Create or edit `backend/.env` with the following content:
    ```env
    # AI Provider
    DASHSCOPE_API_KEY=your_dashscope_api_key

    # CMS Integration (Optional)
    CMS_URL=https://your-cms-url.com
    CMS_COLLECTION=posts
    CMS_EMAIL=your_email
    CMS_PASSWORD=your_password
    CMS_USER_COLLECTION=users
    POLL_INTERVAL=60

    # Security
    SECRET_KEY=your_secret_key_generated_by_openssl
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    ```

5.  Run the Server:
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
    ```
    The API will be available at `http://localhost:8001`. API Docs at `http://localhost:8001/docs`.

### 2. Frontend Setup

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

3.  Run the Development Server:
    ```bash
    npm run dev
    ```
    The application will be available at `http://localhost:5173`.

## 🏭 Production (PM2)

### Backend (PM2)

1.  Ensure the backend virtualenv is created and dependencies are installed:
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate
    pip install -r ../requirements.txt
    ```

2.  Install PM2 and start the API:
    ```bash
    npm i -g pm2
    pm2 start backend/ecosystem.config.cjs
    pm2 status
    pm2 logs api
    ```

### Frontend (Build)

```bash
cd frontend
npm install
npm run build
```

## 📄 Export (DOCX)

-   **Endpoint**: `POST /api/intel/export`
-   **Data Source**:
    -   If `ids` are provided, the API exports items in the same order as `ids`.
    -   If some `ids` are not found in the database, the API falls back to the hot-stream cache and persists them to the database during export.
    -   If `ids` are not provided, the API exports by filters (`type/q/range`) with `limit=1000`.
-   **DOCX Layout (per item)**:
    1.  拟投栏目：`tag1 / tag2 / ...`
    2.  事件时间：`time`
    3.  价值点：`summary`
    4.  标题（居中加粗）：`title`
    5.  正文：`content`（为空时回退到 `summary`）
    6.  （来源信息）：`来源 / 原标题 / 来源URL`

## 🧪 Tests

This repo uses runnable Python scripts under `tests/` for validation.

-   DOCX export format test:
    ```bash
    python tests/test_export_docx_format.py
    ```
    This test generates a DOCX, reads it back, and asserts the paragraph order and content.

Some HTTP-flow tests use `BASE_URL = "http://localhost:8000"` in the script; adjust it to your actual API base (e.g. `http://localhost:8001`) if needed.

## 📂 Project Structure

```
system_mvp/
├── requirements.txt
├── backend/
│   ├── app/
│   │   ├── agent/          # AI Agent logic (Orchestrator, Refiner)
│   │   ├── routes/         # API Endpoints (Auth, Intel, Agent)
│   │   ├── services/       # Business logic (Pollers, Auth Utils)
│   │   ├── crud.py         # Database operations
│   │   ├── models.py       # Pydantic models
│   │   ├── db_models.py    # SQLAlchemy models
│   │   └── main.py         # App entry point
│   ├── ecosystem.config.cjs
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Application pages
│   │   ├── context/        # React Context (Auth)
│   │   ├── hooks/          # Custom Hooks
│   │   ├── api.ts          # API Client
│   │   └── App.tsx
│   └── package.json
├── tests/
└── readme.md
```

## 🔍 Key Concepts

-   **Poller**: A service that runs in the background (or on schedule) to fetch raw data from external sources.
-   **Orchestrator**: The central brain that coordinates data flow between the Poller, Database, and AI Agents.
-   **Refinement**: The process of taking raw, potentially unstructured data and using LLMs to extract key information (Summary, Tags, Sentiment) and standardize the format.

## 🤝 Contributing

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'Add some amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.
