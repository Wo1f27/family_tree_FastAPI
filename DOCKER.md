# ===========================================
# Family Tree - Docker Setup
# ===========================================

## Быстрый старт

### 1. Клонировать репозиторий
```bash
git clone <repo-url>
cd family_tree_FastAPI
```

### 2. Создать .env
```bash
cp .env.example .env
# Отредактировать .env
```

### 3. Собрать и запустить
```bash
docker compose build
docker compose up -d
```

**Миграции применяются автоматически при старте контейнера!**

### 4. Проверить
```bash
curl http://localhost:8000/health
# {"status":"ok"}

# Проверить логи миграций
docker compose logs app
```

---

## Структура

```
family_tree_FastAPI/
├── Dockerfile              # Multi-stage build
├── docker-compose.yml      # Оркестрация
├── .dockerignore           # Исключения из образа
├── .env.example            # Шаблон переменных
├── nginx/
│   └── default.conf        # Nginx конфиг
├── .github/
│   └── workflows/
│       └── deploy.yml      # CI/CD
└── DEPLOY.md               # Полная инструкция
```

---

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `DB_HOST` | Адрес PostgreSQL | `127.0.0.1` |
| `DB_PORT` | Порт PostgreSQL | `5432` |
| `DB_NAME` | Имя БД | `familytree` |
| `DB_USER` | Пользователь БД | `familytree` |
| `DB_PASSWORD` | Пароль БД | `CHANGE_ME_SECURE_PASSWORD` |
| `FAMILY_TREE_DB_URL` | Полный URL БД | генерируется из вышеуказанных |
| `FAMILY_TREE_HOST` | Хост для Gunicorn | `0.0.0.0` |
| `FAMILY_TREE_PORT` | Порт для Gunicorn | `8000` |
| `FAMILY_TREE_DEBUG` | Debug режим | `false` |
| `FAMILY_TREE_DEBUG_SQL` | Логирование SQL | `false` |
| `DOMAIN` | Домен для SSL | `your-domain.com` |

---

## Volumes

| Volume | Где хранится | Содержимое |
|--------|--------------|------------|
| `uploads_data` | `/var/lib/docker/volumes/...` | Фото пользователей |

**Данные НЕ удалятся при `docker compose down`**

---

## Команды

```bash
# Запуск
docker compose up -d

# Остановка
docker compose down

# Логи
docker compose logs -f app
docker compose logs -f nginx

# Перезапуск
docker compose restart

# Пересборка
docker compose up -d --build

# Проверка
docker compose ps
docker compose exec app python -c "print('ok')"
```

---

## CI/CD

При push в `main`:
1. Запускаются тесты
2. Собирается Docker образ
3. Образ пушится в GHCR
4. Деплой на VPS через SSH

### Secrets для GitHub Actions
- `VPS_HOST` — IP сервера
- `VPS_USER` — пользователь (familytree)
- `VPS_SSH_KEY` — приватный SSH ключ
