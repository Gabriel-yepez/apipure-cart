import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logger import setup_logging, logger
from app.auth.routes import router as auth_router
from app.users.routes import router as users_router
from app.products.routes import router as products_router
from app.favorites.routes import router as favorites_router
from app.transactions.routes import router as transactions_router

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
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    formatted_process_time = "{:.2f}ms".format(process_time)
    
    logger.info(
        f"Method: {request.method} Path: {request.url.path} "
        f"Status: {response.status_code} Duration: {formatted_process_time}"
    )
    
    return response

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
    return {"status": "ok", "version": settings.APP_VERSION}
