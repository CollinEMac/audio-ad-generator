FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /code

COPY pyproject.toml uv.lock /code/

RUN uv sync --frozen --no-install-project

COPY ./app /code/app

RUN uv sync --frozen

CMD ["uv", "run", "fastapi", "run", "app/main.py", "--port", "80"]
