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

# Настройка CORS для клиентских запросов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Адрес фронтенда
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
)

# Подключаем роуты
app.include_router(router)


# Startup event
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
