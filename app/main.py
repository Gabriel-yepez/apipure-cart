import time
import logging
import uuid
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.trace.logger import setup_logging, logger, set_request_id
from app.auth.routes import router as auth_router
from app.users.routes import router as users_router
from app.products.routes import router as products_router
from app.favorites.routes import router as favorites_router
from app.transactions.routes import router as transactions_router
from app.apiResponse.schemas import create_response

# Initialize logging
setup_logging()

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="E-commerce backend API with FastAPI and Supabase",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── Middleware ──────────────────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Generate a unique request ID for tracing
    request_id = str(uuid.uuid4())
    token = set_request_id(request_id)
    
    start_time = time.time()
    
    client_host = request.client.host if request.client else "unknown"
    
    try:
        response: Response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        formatted_process_time = "{:.2f}ms".format(process_time)
        
        # Log message with status-appropriate level
        log_msg = (
            f"Client: {client_host} | "
            f"Method: {request.method} | "
            f"URL: {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Duration: {formatted_process_time}"
        )
        
        if response.status_code >= 500:
            logger.error(log_msg)
        elif response.status_code >= 400:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
            
        # Add request ID to response headers
        response.headers["X-Request-Id"] = request_id
        return response

    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        formatted_process_time = "{:.2f}ms".format(process_time)
        
        logger.error(
            f"Client: {client_host} | "
            f"Method: {request.method} | "
            f"URL: {request.url.path} | "
            f"Exception: {str(e)} | "
            f"Duration: {formatted_process_time}",
            exc_info=True # This includes the traceback
        )
        # Re-raise so FastAPI can handle it (or common error handlers)
        raise e

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(auth_router,         prefix=f"{PREFIX}/auth",         tags=["Auth"])
app.include_router(users_router,        prefix=f"{PREFIX}/users",        tags=["Users"])
app.include_router(products_router,     prefix=f"{PREFIX}/products",     tags=["Products"])
app.include_router(favorites_router,    prefix=f"{PREFIX}/favorites",    tags=["Favorites"])
app.include_router(transactions_router, prefix=f"{PREFIX}/transactions", tags=["Transactions"])


@app.get("/", tags=["Health"])
async def health_check():
    data = {"status": "ok", "version": settings.APP_VERSION}
    return create_response(data=data, messages="API is healthy")
