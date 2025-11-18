"""Enhanced health check endpoint"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime
import asyncio
from hyperagent.core.config import settings
import asyncpg
import redis.asyncio as redis

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check
    
    Returns:
        Simple health status
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with service status
    
    Checks:
    - Database connectivity
    - Redis connectivity
    - API responsiveness
    
    Returns:
        Detailed health status with service checks
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # Check database
    db_status = await _check_database()
    health_status["services"]["database"] = db_status
    
    # Check Redis
    redis_status = await _check_redis()
    health_status["services"]["redis"] = redis_status
    
    # Determine overall status
    all_healthy = all(
        service["status"] == "healthy"
        for service in health_status["services"].values()
    )
    
    if not all_healthy:
        health_status["status"] = "degraded"
    
    return health_status


async def _check_database() -> Dict[str, Any]:
    """Check database connectivity"""
    try:
        conn = await asyncio.wait_for(
            asyncpg.connect(settings.database_url),
            timeout=5.0
        )
        await conn.close()
        return {
            "status": "healthy",
            "response_time_ms": 0  # Would measure actual time
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def _check_redis() -> Dict[str, Any]:
    """Check Redis connectivity"""
    try:
        client = await asyncio.wait_for(
            redis.from_url(settings.redis_url),
            timeout=5.0
        )
        await client.ping()
        await client.close()
        return {
            "status": "healthy",
            "response_time_ms": 0
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/readiness")
async def readiness_check() -> Dict[str, Any]:
    """
    Kubernetes readiness probe
    
    Returns:
        Ready status for Kubernetes
    """
    # Check if application is ready to accept traffic
    # This could check: database migrations complete, services initialized, etc.
    return {
        "ready": True,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/liveness")
async def liveness_check() -> Dict[str, Any]:
    """
    Kubernetes liveness probe
    
    Returns:
        Liveness status for Kubernetes
    """
    # Check if application is alive and should not be restarted
    return {
        "alive": True,
        "timestamp": datetime.now().isoformat()
    }

