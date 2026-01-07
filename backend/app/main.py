from fastapi import FastAPI, Request
from app.routes import intel, agent, auth
from app.cors import setup_cors
from app.agent.orchestrator import orchestrator
from app.services.poller import article_poller
from app.services.payload_poller import payload_poller
from app.services.mock_poller import mock_poller
from app.database import engine, Base
import asyncio
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Intel Aggregation API")

# Setup CORS
setup_cors(app)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    print(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"Request completed: {request.method} {request.url} - Status: {response.status_code} - Time: {process_time:.4f}s")
    return response

# Include Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(intel.router, prefix="/api/intel", tags=["intel"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])

@app.on_event("startup")
async def startup_event():
    # Run analysis in background to not block startup
    asyncio.create_task(orchestrator.analyze_data_file())

    # Auto-start pollers if configured via ENV
    cms_url = os.getenv("CMS_URL")
    cms_collection = os.getenv("CMS_COLLECTION", "posts")
    cms_email = os.getenv("CMS_EMAIL")
    cms_password = os.getenv("CMS_PASSWORD")
    cms_user_collection = os.getenv("CMS_USER_COLLECTION", "users")
    poll_interval = int(os.getenv("POLL_INTERVAL", "10"))
    
    poller_started = False

    if cms_url and cms_email and cms_password:
        print(f"Auto-starting PayloadPoller with URL: {cms_url}")
        payload_poller.configure(cms_url, cms_collection, cms_email, cms_password, cms_user_collection, poll_interval)
        await payload_poller.start()
        poller_started = True
    else:
        print("PayloadPoller not configured (missing env vars). Skipping auto-start.")

    article_base_url = os.getenv("ARTICLE_POLLER_URL")
    if article_base_url:
        print(f"Auto-starting ArticlePoller with URL: {article_base_url}")
        article_poller.configure(article_base_url)
        await article_poller.start()
        poller_started = True
    else:
        print("ArticlePoller not configured (missing env vars). Skipping auto-start.")

    # If no real pollers configured, start Mock Poller for demo
    if not poller_started:
        print("No real pollers configured. MockPoller is disabled by request.")
        # await mock_poller.start()

@app.get("/")
async def root():
    return {"message": "Intel Agent API is running"}
