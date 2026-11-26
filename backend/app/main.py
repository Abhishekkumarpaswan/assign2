import time
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.seed_data import seed_database
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.orders import router as orders_router
from backend.app.api.v1.tickets import router as tickets_router
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.refunds import router as refunds_router
from backend.app.api.v1.escalations import router as escalations_router
from backend.app.api.v1.policies import router as policies_router

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}'
)
logger = logging.getLogger("kinetic_app")

# Initialize database tables safely
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.warning(f"Initial table creation deferred to startup: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Full-stack E-Commerce AI Support & Refund Operations Engine with business guardrails and multi-turn AI reasoning.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to seed database
@app.on_event("startup")
def on_startup():
    logger.info("Initializing database and ensuring seed records...")
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    logger.info("Kinetic E-Commerce AI Support Backend started.")

# Request timing & structured audit middleware
@app.middleware("http")
async def audit_logging_middleware(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
        if request.url.path not in ["/health", "/docs", "/openapi.json"]:
            logger.info(f"Method={request.method} Path={request.url.path} Status={response.status_code} DurationMs={process_time:.2f}")
        return response
    except Exception as exc:
        process_time = (time.time() - start_time) * 1000
        logger.error(f"Method={request.method} Path={request.url.path} Exception={str(exc)} DurationMs={process_time:.2f}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred. Please contact support."}
        )

from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Register API routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(orders_router, prefix=settings.API_V1_STR)
app.include_router(tickets_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(refunds_router, prefix=settings.API_V1_STR)
app.include_router(escalations_router, prefix=settings.API_V1_STR)
app.include_router(policies_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "max_auto_refund_limit": settings.MAX_AUTO_REFUND_AMOUNT
    }

# Mount static frontend build if present
DIST_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        file_path = DIST_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(DIST_DIR / "index.html")
else:
    @app.get("/", tags=["Root"])
    def root():
        return {
            "message": f"Welcome to {settings.PROJECT_NAME} API",
            "docs": "/docs",
            "api_v1": settings.API_V1_STR
        }
