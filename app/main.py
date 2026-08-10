import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.application import router as applications_router
from app.core.config import settings
from middleware.logging import LoggingMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s-%(name)s-%(levelname)s-%(message)s"
)
logger=logging.getLogger("bridgescore")


@asynccontextmanager
async def lifespan(app:FastAPI):
    logger.info("Initializing BridgeScore environment")
    logger.info(f"Project: {settings.project_name} v{settings.version}")
    logger.info(f"API preflix:{settings.api_v1_str}")
    logger.info(f"Production:{settings.production}")
    logger.info(f"Debug mode:{settings.debug}")
    logger.info(f"Developer mode:{settings.is_dev_mode}")
    logger.info("Startup complete -ready to process applications")
    yield
    logger.info("Shutting down Bridgescore")

app=FastAPI(
    title=settings.project_name,
    description="Autonomous Multi-Agent Credit Orchestartion System for Nepal's Agriculture",
    version=settings.version,
    docs_url=f"{settings.api_v1_str}/docs" if not settings.production else None,
    redoc_url=f"{settings.api_v1_str}/redocs" if not settings.production else None,
    lifespan=lifespan,
)    

app.add_middleware(LoggingMiddleware)
if settings.allow_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],

    )



app.include_router(
    applications_router,
    prefix=settings.api_v1_str
)


@app.get("/",tags=["Health"])
def root():
    return {
        "system":settings.project_name,
        "status":"operational",
        "version":settings.version,

    }

@app.get("/health",tags=["Health"])
def health():
    return {"status":"ok"}    



