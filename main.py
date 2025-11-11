from fastapi import FastAPI
from fastapi.logger import logger

def main():
    print("Hello from devops-engineer-from-scratch-project-313!")


if __name__ == "__main__":
    main()


app = FastAPI()


@app.get("/ping")
def read_root():
    logger.info("Получен запрос, отправляем pong")
    return 'pong'