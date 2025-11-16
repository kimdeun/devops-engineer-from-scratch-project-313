FROM python:3.11-slim
WORKDIR /
COPY . .
RUN apt-get update && apt-get install -y make
RUn make install
RUN make build
RUN make ping-pong
ENV DSN=https://a8c75166e50c7c0f2f844e7e7c4d53ac@o4510374943195136.ingest.de.sentry.io/4510374946078800