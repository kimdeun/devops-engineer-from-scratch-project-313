import os
from fastapi import FastAPI
from fastapi.logger import logger
from fastapi.testclient import TestClient
from fastapi import FastAPI
import sentry_sdk


def main():
    print("Hello from devops-engineer-from-scratch-project-313!")


if __name__ == "__main__":
    main()

sentry_sdk.init(
    dsn=os.getenv('DSN'),
    send_default_pii=True,
)

app = FastAPI()

@app.get("/ping")
def get_ping():
    logger.info("Получен запрос, отправляем pong")
    return "pong"

@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0
