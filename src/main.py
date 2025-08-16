import os
from fastapi import FastAPI, APIRouter, status, HTTPException
from redis.exceptions import RedisError
from pathlib import Path
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from storage.redis_client import RedisClient

app = FastAPI()
router = APIRouter()


##################################
#  Endpoints

@router.get("/healthz")
async def healthz():
    """
    Return a JSONResponse indicating the service is running (health check).
    
    Returns:
        fastapi.responses.JSONResponse: HTTP 200 response with JSON body
        {"status": "200", "message": "PromptSafely server running"}.
    """
    return  JSONResponse(
        status_code= status.HTTP_200_OK,
        content= {"status": "200", "message": "PromptSafely server running"}
    )
       
@router.get("/readyz")
async def readyz():
    """
    Check readiness of dependent services (Redis) and return a readiness message.
    
    Performs a Redis PING using RedisClient().client.ping(). On success returns {"message": "All services are up"}. If the ping is falsy, raises HTTPException(status_code=503, detail="Redis not responding"). If a RedisError occurs, it is converted into HTTPException(status_code=503) with the Redis error message included in the detail.
    
    Returns:
        dict: JSON-serializable readiness message.
    
    Raises:
        HTTPException: with status 503 when Redis is unreachable or returns an error.
    """
    try:
        if RedisClient().client.ping():                 
            return {"message": "All services are up"}
        raise HTTPException(status_code=503, detail="Redis not responding")
    except RedisError as e:
        raise HTTPException(503, detail=f"Redis error: {str(e)}")

@router.get("/metrices")
async def metrices():
    """
    Return a small JSON object indicating the Prometheus metrics endpoint.
    
    This endpoint is a placeholder that should expose the Prometheus registry/metrics.
    
    Returns:
        dict: JSON-serializable mapping with a "message" key describing the endpoint.
    """
    return {"message": "expose Prometheus registry"}
    
app.include_router(router, prefix="/v1")