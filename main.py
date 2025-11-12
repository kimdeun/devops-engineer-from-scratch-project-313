from fastapi import FastAPI
from fastapi.logger import logger
from fastapi.testclient import TestClient


def main():
    print("Hello from devops-engineer-from-scratch-project-313!")


if __name__ == "__main__":
    main()


app = FastAPI()


@app.get("/ping")
def get_ping():
    logger.info("Получен запрос, отправляем pong")
    return "pong"
