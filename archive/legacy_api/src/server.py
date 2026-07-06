from fastapi import FastAPI, status
from fastapi.concurrency import asynccontextmanager
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from src.crons import shutdown_scheduler, start_scheduler
from src.routers.admin_router import admin_router
from src.routers.chat_router import chat_router
from src.routers.focus_router import focus_router
from src.routers.sherpa_router import sherpa_router
from src.routers.user_router import user_router
from src.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    shutdown_scheduler()


# Create FastAPI app
app = FastAPI(lifespan=lifespan)

# Allow CORS for all origins for simplicity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(admin_router, prefix="/admin")
app.include_router(sherpa_router, prefix="/sherpa")
app.include_router(focus_router, prefix="/focus")
app.include_router(chat_router, prefix="/chat")
app.include_router(user_router, prefix="/user")


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request, exc):
    content = {
        "detail": exc.errors(),
    }
    logger.error("Request Validation Error:", content)
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=content)


@app.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(request, exc):
    content = {
        "detail": exc.errors(),
    }
    logger.error("Response Validation Error:", content)
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=content)


# Root
@app.get("/")
async def root():
    return {"message": "Hello World"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Mindsherpa API",
        version="0.0.1",
        summary="Mindsherpa API",
        description="Mindsherpa API",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {"url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"}
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
