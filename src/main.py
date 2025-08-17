from fastapi import FastAPI, APIRouter, status, HTTPException
from redis.exceptions import RedisError
from fastapi.responses import JSONResponse
from storage.redis_client import RedisClient
from prometheus_client import make_asgi_app
from moniter.metrics import REDACTIONS_TOTAL,REQUESTS_TOTAL

app = FastAPI()
router = APIRouter()
redis_client = RedisClient().client

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
        if redis_client.ping():
            return  JSONResponse(
                status_code= status.HTTP_200_OK,
                content= {"status": "200", "message": "All services are up"}
            )             
        raise HTTPException(status_code=503, detail="Redis not responding")
    except RedisError as e:
        raise HTTPException(status_code=503, detail="Redis error") from e

#  /metrics/ endpoint for promethus client
metrices_app = make_asgi_app()
app.mount("/metrics/",metrices_app)
    
app.include_router(router, prefix="/v1")