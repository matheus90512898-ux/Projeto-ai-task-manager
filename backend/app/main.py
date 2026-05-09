import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.api.routes import auth, tasks, pdf
from app.core.database import Base, engine
from app.core.limiter import limiter

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

security = HTTPBearer()

app = FastAPI(
    title="AI Task Manager",
    description="Gerenciador de tarefas inteligente com IA e leitura de PDFs",
    version="2.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Erro interno", extra={"url": str(request.url), "error": str(exc)})
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor."},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai-task-manager-pearl-alpha.vercel.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Cache-Control"] = "no-store"
    for header in ["X-Powered-By", "X-Real-IP", "X-Forwarded-For"]:
        if header in response.headers:
            del response.headers[header]
    return response

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(pdf.router)

@app.get("/health")
@limiter.limit("10/minute")
def health_check(request: Request):
    return {"status": "ok", "version": "2.0.0"}
