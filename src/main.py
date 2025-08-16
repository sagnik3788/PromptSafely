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
    return  JSONResponse(
        status_code= status.HTTP_200_OK,
        content= {"status": "200", "message": "PromptSafely server running"}
    )
       
@router.get("/readyz")
async def readyz():
    try:
        if RedisClient().client.ping():                 
            return {"message": "All services are up"}
        raise HTTPException(status_code=503, detail="Redis not responding")
    except RedisError as e:
        raise HTTPException(503, detail=f"Redis error: {str(e)}")

@router.get("/metrices")
async def metrices():
    return {"message": "expose Prometheus registry"}
    
app.include_router(router, prefix="/v1")