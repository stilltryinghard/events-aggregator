FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN addgroup --system --gid 1000 appuser && \
    adduser --system --uid 1000 --ingroup appuser appuser

WORKDIR /code

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser alembic.ini run.sh ./
COPY --chown=appuser:appuser alembic ./alembic

ENV PATH="/code/.venv/bin:$PATH"

USER appuser

CMD ["sh", "./run.sh"]