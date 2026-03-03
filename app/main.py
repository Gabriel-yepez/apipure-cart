from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.products.router import router as products_router
from app.favorites.router import router as favorites_router
from app.transactions.router import router as transactions_router

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="E-commerce backend API with FastAPI and Supabase",
    docs_url="/docs",
    redoc_url="/redoc",
)

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
