# ===========================================
# Family Tree - Dockerfile
# ===========================================
# Multi-stage build для минимального образа

# -------------------------------------------
# Stage 1: Build dependencies
# -------------------------------------------
FROM python:3.13-slim AS builder

WORKDIR /build

# Устанавливаем зависимости системы
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем только requirements для кэширования
COPY pyproject.toml .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir --prefix=/install -r <(python -c "import tomllib; print('\n'.join(tomllib.load(open('pyproject.toml'))['project']['dependencies']))")

# -------------------------------------------
# Stage 2: Production image
# -------------------------------------------
FROM python:3.13-slim

# Метаданные
LABEL maintainer="familytree@example.com"
LABEL description="Family Tree Web Application"

# Переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:$PATH"

# Устанавливаем зависимости системы
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system familytree \
    && useradd --system --gid familytree familytree

# Копируем установленные пакеты из builder
COPY --from=builder /install /install

# Создаём рабочую директорию
WORKDIR /app

# Копируем исходный код
COPY --chown=familytree:familytree src/ ./src/

# Создаём директории для данных
RUN mkdir -p /app/uploads /app/static && chown -R familytree:familytree /app

# Переключаемся на non-root пользователя
USER familytree

# Открываем порт
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Запускаем Gunicorn
CMD ["gunicorn", "familytree.main:app", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--graceful-timeout", "30", \
     "--timeout", "120", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "50"]
