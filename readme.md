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

## � Prerequisites

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
    pip install -r requirements.txt
    ```

4.  Configure Environment Variables:
    Create a `.env` file in the `backend` directory with the following content:
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
    ACCESS_TOKEN_EXPIRE_MINUTES=1440
    ```

5.  Run the Server:
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    The API will be available at `http://localhost:8000`. API Docs at `http://localhost:8000/docs`.

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

## 📂 Project Structure

```
system_mvp/
├── backend/
│   ├── app/
│   │   ├── agent/          # AI Agent logic (Orchestrator, Refiner)
│   │   ├── routes/         # API Endpoints (Auth, Intel, Agent)
│   │   ├── services/       # Business logic (Pollers, Auth Utils)
│   │   ├── crud.py         # Database operations
│   │   ├── models.py       # Pydantic models
│   │   ├── db_models.py    # SQLAlchemy models
│   │   └── main.py         # App entry point
│   ├── requirements.txt
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
└── README.md
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
