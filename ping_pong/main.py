import os
from fastapi import FastAPI
from fastapi.logger import logger
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
from ping_pong.database import create_db_and_tables
from ping_pong.routes import router


def main():
    print("Hello from devops-engineer-from-scratch-project-313!")


if __name__ == "__main__":
    main()

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


@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0
