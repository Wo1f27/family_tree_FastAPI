# ===========================================
# Family Tree - Инструкция по деплою на VPS
# ===========================================

## 1. Подготовка сервера

### Установка PostgreSQL
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y

# Создаём базу и пользователя
sudo -u postgres psql
CREATE DATABASE familytree;
CREATE USER familytree WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE familytree TO familytree;
\q

# Настраиваем автозапуск
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### Установка Docker и Docker Compose
```bash
# Устанавливаем Docker
curl -fsSL https://get.docker.com | sh

# Добавляем пользователя в группу docker
sudo usermod -aG docker $USER

# Устанавливаем Docker Compose plugin
sudo apt install docker-compose-plugin -y
```

### Создаём пользователя и директорию
```bash
sudo useradd -m -s /bin/bash familytree
sudo mkdir -p /home/familytree/family_tree_FastAPI
sudo chown -R familytree:familytree /home/familytree
```

---

## 2. Настройка проекта

### Копируем файлы на сервер
```bash
# На локальной машине
cd /path/to/family_tree_FastAPI
scp -r . familytree@YOUR_VPS_IP:/home/familytree/family_tree_FastAPI/
```

### Создаём .env
```bash
ssh familytree@YOUR_VPS_IP
cd /home/familytree/family_tree_FastAPI
cp .env.example .env
nano .env
```

Заполняем:
```bash
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=familytree
DB_USER=familytree
DB_PASSWORD=your_secure_password

FAMILY_TREE_DB_URL=postgresql+psycopg2://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
FAMILY_TREE_HOST=0.0.0.0
FAMILY_TREE_PORT=8000
FAMILY_TREE_DEBUG=false
FAMILY_TREE_DEBUG_SQL=false

DOMAIN=your-domain.com
```

### Настраиваем nginx
```bash
# Редактируем домен в nginx конфиге
sed -i "s/\${DOMAIN}/your-domain.com/g" nginx/default.conf
```

---

## 3. Запуск

### Собираем и запускаем
```bash
cd /home/familytree/family_tree_FastAPI

# Собираем образ
docker compose build

# Запускаем (автоматически применяет миграции)
docker compose up -d

# Проверяем
docker compose ps
docker compose logs -f app
```

### Открываем порты
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 4. SSL сертификат

### Получаем сертификат
```bash
# Устанавливаем certbot
sudo apt install certbot -y

# Получаем сертификат
sudo certbot --nginx -d your-domain.com
```

### Обновляем nginx конфиг с реальным доменом
```bash
# Заменяем плейсхолдер на реальный домен
sed -i "s/\${DOMAIN}/your-domain.com/g" nginx/default.conf

# Перезапускаем
docker compose restart nginx
```

### Автоматическое обновление
```bash
# Добавляем cron job
sudo crontab -e
# Добавляем строку:
0 0 * * * certbot renew --quiet && docker compose exec nginx nginx -s reload
```

---

## 5. GitHub Actions

### Настройка secrets на GitHub
1. Открой репозиторий → Settings → Secrets and variables → Actions
2. Добавь secrets:
   - `VPS_HOST` — IP сервера
   - `VPS_USER` — familytree
   - `VPS_SSH_KEY` — приватный SSH ключ

### Генерация SSH ключа
```bash
ssh-keygen -t ed25519 -C "github-actions"
cat ~/.ssh/id_ed25519.pub  # Копируй публичный ключ
```

### Добавляем публичный ключ на сервер
```bash
ssh familytree@YOUR_VPS_IP
mkdir -p ~/.ssh
echo "ПУБЛИЧНЫЙ_КЛЮЧ" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

---

## 6. Бэкапы

### Бэкап БД
```bash
# Ручной бэкап
sudo -u postgres pg_dump familytree > /home/familytree/backups/familytree_$(date +%Y%m%d).sql

# Автоматический (добавляем в crontab)
0 2 * * * sudo -u postgres pg_dump familytree > /home/familytree/backups/familytree_$(date +\%Y\%m\%d).sql
```

### Бэкап фото
```bash
# Ручной
cp -r /var/lib/docker/volumes/familytree_uploads_data/_data /home/familytree/backups/photos/

# Автоматический
0 3 * * * cp -r /var/lib/docker/volumes/familytree_uploads_data/_data /home/familytree/backups/photos/
```

---

## 7. Полезные команды

```bash
# Статус контейнеров
docker compose ps

# Логи
docker compose logs -f app
docker compose logs -f nginx

# Перезапуск
docker compose restart

# Остановка
docker compose down

# Пересборка и запуск
docker compose up -d --build

# Обновление с GitHub
cd /home/familytree/family_tree_FastAPI
git pull origin main
docker compose down
docker compose up -d

# Проверка здоровья
curl http://localhost:8000/health

# Проверка SSL
curl -I https://your-domain.com

# Проверить логи миграций
docker compose logs app | grep -i alembic

# Применить миграции вручную (если нужно)
docker compose exec app alembic upgrade head

# Проверить текущую версию миграции
docker compose exec app alembic current
```
