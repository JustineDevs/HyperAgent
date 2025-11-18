"""FastAPI main application"""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from hyperagent.core.config import settings
from hyperagent.api.routes import workflows, contracts, deployments, metrics, auth, health, templates, networks
from hyperagent.api.websocket import websocket_endpoint
from hyperagent.api.middleware.rate_limit import RateLimitMiddleware, RateLimiter
from hyperagent.api.middleware.security import SecurityHeadersMiddleware, InputSanitizationMiddleware
from hyperagent.cache.redis_manager import RedisManager
import redis.asyncio as redis

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Agent Platform for On-Chain Smart Contract Generation",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    contact={
        "name": "HyperAgent Team",
        "email": "info@hyperagent.dev"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Security headers middleware (add first to apply to all responses)
app.add_middleware(SecurityHeadersMiddleware)

# Input sanitization middleware
app.add_middleware(InputSanitizationMiddleware)

# CORS middleware
cors_origins = getattr(settings, "cors_origins", "*").split(",") if hasattr(settings, "cors_origins") else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware (if enabled)
if getattr(settings, "enable_rate_limiting", False):
    redis_manager = RedisManager(settings.redis_url)
    rate_limiter = RateLimiter(redis_manager)
    app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(workflows.router)
app.include_router(contracts.router)
app.include_router(deployments.router)
app.include_router(templates.router)
app.include_router(networks.router)
app.include_router(metrics.router)


# Health check routes are now in health.py router


@app.websocket("/ws/workflow/{workflow_id}")
async def websocket_workflow(websocket: WebSocket, workflow_id: str):
    """WebSocket endpoint for real-time workflow updates"""
    await websocket_endpoint(websocket, workflow_id)

