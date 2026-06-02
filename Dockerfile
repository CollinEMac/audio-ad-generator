# Frontend
FROM node:20-slim AS frontend
WORKDIR /build
COPY package.json tsconfig.json ./
RUN npm install
COPY src/ ./src/
RUN npm run build

# Backend
FROM python:3.14-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /code
COPY pyproject.toml uv.lock /code/
RUN uv sync --frozen --no-install-project
COPY ./app /code/app
COPY ./static /code/static
COPY --from=frontend /build/static/dist /code/static/dist
RUN uv sync --frozen
CMD ["uv", "run", "fastapi", "run", "app/main.py", "--port", "80"]
