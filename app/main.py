import os
from fastapi import FastAPI
from fastapi.logger import logger
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
from app.database import create_db_and_tables
from app.routes import router


sentry_sdk.init(
    dsn=os.getenv("DSN"),
    send_default_pii=True,
)

app = FastAPI()


cors_origins_env = os.getenv("CORS_ORIGINS", "*")
if cors_origins_env == "*":
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/ping")
def get_ping():
    logger.info("Получен запрос, отправляем pong")
    return "pong"
