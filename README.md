# HobbyMate
[![CI](https://github.com/Werner029/HobbymateProject/actions/workflows/ci.yml/badge.svg)](https://github.com/Werner029/HobbymateProject/actions/workflows/ci.yml)
[![CodeQL](https://github.com/Werner029/HobbymateProject/actions/workflows/codeql.yml/badge.svg)](https://github.com/Werner029/HobbymateProject/actions/workflows/codeql.yml)
[![Dependabot](https://img.shields.io/badge/Dependabot-enabled-brightgreen?logo=dependabot)](https://github.com/Werner029/HobbymateProject/security/dependabot)
![Coverage](backend_helper_course/coverage.svg?raw=true)

> **Платформа для поиска собеседников по интересам с умным алгоритмом метчинга**

HobbyMate - это современная веб-платформа, которая помогает людям находить собеседников на основе общих интересов. Система использует векторные представления интересов и алгоритм нахождения клик создания оптимальных групп и приватных диалогов.

## Основные возможности

- **Умный поиск собеседников** - алгоритм на основе векторных представлений интересов
- **Групповые чаты** - автоматическое формирование групп по интересам
- **Личные диалоги** - приватное общение между пользователями
- **Геолокация** - поиск собеседников в вашем городе
- **Уведомления в реальном времени** - WebSocket для мгновенных уведомлений
- **Современный UI** - адаптивный интерфейс с поддержкой темной темы
- **Безопасность** - аутентификация через Keycloak

## ️ Архитектура проекта

### Backend (Django)
- **Django 5.2** с Django REST Framework
- **PostgreSQL** с PostGIS для геолокации
- **Redis** для кэширования и очередей
- **Celery** для фоновых задач
- **Django Channels** для WebSocket-соединений для real-time и чата
- **Keycloak** для аутентификации
- **ELK Stack** для логирования

### Frontend (React)
- **React 19** с Vite
- **Tailwind CSS** для стилизации
- **React Router** для навигации
- **Axios** для HTTP-запросов
- **Keycloak JS** для аутентификации

### Инфраструктура
- **Docker Compose** для оркестрации
- **Nginx** как reverse proxy
- **Yandex Cloud Storage** для файлов
- **Elasticsearch + Kibana** для аналитики

## Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- Git

### Установка и запуск

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/Werner029/HobbymateProject
   ```

2. ```bash
   cp .env.example .env
   cp env.keycloak.example .env.keycloak
   ```

3. **Запустите проект:**
   ```bash
   docker compose up -d
   ```

4. **Выполните миграции:**
   ```bash
   docker compose exec backend python manage.py migrate
   ```

5. **Создайте суперпользователя:**
   ```bash
   docker compose exec backend python manage.py createsuperuser
   ```

### Доступ к сервисам

- **Frontend:** http://localhost:80
- **Backend API:** http://localhost:8000
- **Keycloak:** http://localhost:8080/keycloak
- **Kibana:** http://localhost:5601
- **Elasticsearch:** http://localhost:9200

## CI (GitHub Actions)

CI запускается на push/pull_request и включает:

Python: black, isort, flake8; pytest с Postgres 17 (PostGIS + pgvector) и Redis

Frontend: ESLint (--max-warnings=0), Prettier --check

Инфра: hadolint (Dockerfile), yamllint + docker compose config -q, jq (JSON‑lint), gitleaks (секреты)

OpenAPI: проверка актуальности схемы

##  Разработка

### Структура проекта

```
hobbymate/
├── backend_helper_course/         # Django backend
│   ├── api/                       # API endpoints
│   ├── dialogs/                   # Модели диалогов и чатов
│   ├── docs/                      # OpenApi спецификация
│   ├── users/                     # Пользователи и аутентификация
│   ├── interests/                 # Система интересов
│   ├── feedback/                  # Обратная связь
│   └── helper/                    # Настройки Django
├── frontend_helper_course/        # React frontend
│   ├── src/                       # Исходный код
│   └── public/                    # Статические файлы
└── docker compose.yaml            # Конфигурация Docker
```

### Основные команды

```bash
# Запуск в режиме разработки
docker compose up -d

# Просмотр логов
docker compose logs -f backend

# Выполнение команд Django
docker compose exec backend python manage.py <command>

# Сборка фронтенда
docker compose exec web npm run build

# Остановка всех сервисов
docker compose down
```
## API (REST & WS)

База: /api/ (за Nginx)

Формат: application/json; charset=utf-8

Аутентификация: JWT от Keycloak - заголовок Authorization: Bearer <token>

Пагинация/фильтры: ?limit=&offset= + query‑params

Ключевые сущности и эндпоинты

Профиль

GET /profile/me/ - свой профиль

PATCH /profile/me/ - частичное обновление

Пользователи

GET /users/?q=&city=&interest= - поиск/фильтры

GET /users/{id}/ - профиль

Интересы

GET /interests/ - 15 базовых интересов (векторизация)

Подбор/матчи

GET /matches?limit=10 - кандидаты по схожести (pgvector; дистанция/оффлайн)

POST /swipe/ - {"target_id": int, "action": "like"|"skip"|"dislike"}; взаимный like создаёт диалог

Диалоги (REST + WS)

GET /dialogs/

GET /dialogs/{id}/messages/

POST /dialogs/{id}/messages/

WS: ws://<host>/ws/dialogs/{id}/

Группы

GET /groups/

POST /groups/

GET /groups/{id}/

Уведомления (WS)

ws://<host>/ws/notifications/ - события: новый матч/сообщение/приглашение

Обратная связь

POST /feedback/

GET /feedback/ - (админ) список обращений

Здоровье

GET /healthcheck/

Фактические роуты смотрите в Swagger/Redoc.

Ошибки (единый формат)
```json
{
  "error_code": "validation_error",
  "message": "Некорректные данные",
  "details": {"field": "обязательное поле"}
}
```
Коды: 400 (валидация), 401 (аутентификация), 403 (нет прав), 404 (не найдено).

## Документация

OpenAPI‑схема: ./openapi.yaml

Интерактивная документация: /api/docs, /api/schema/swagger-ui/ или /api/schema/redoc/

## Конфигурация

### Настройка Keycloak

1. Импортируйте конфигурацию из `hobbymate-realm.json`
2. Настройте клиенты для фронтенда и бэкенда
3. Обновите переменные окружения

### Настройка Yandex Cloud Storage

1. Создайте бакет в Yandex Cloud
2. Получите ключи доступа
3. Обновите переменные `AWS_*` в `.env`

## Мониторинг
 **Логи:** Elasticsearch + Kibana (http://localhost:9200  http://localhost:5601)
 **Метрики:** Prometheus + Grafana
- **Кэш:** Redis (localhost:6379)

## Безопасность и Nginx‑hardening

TLS‑терминация + HSTS; закрыт HTTP → редирект на HTTPS

Ограничения: rate‑limit (limit_req), client_max_body_size, limit_conn

Безопасные заголовки: X-Frame-Options: DENY, X-Content-Type-Options: nosniff, Referrer-Policy: strict-origin-when-cross-origin, Permissions-Policy, Content-Security-Policy

Корректные proxy‑headers: X-Forwarded-For, X-Forwarded-Proto, Host

Таймауты: proxy_read_timeout, send_timeout, keepalive_timeout

Логи в JSON для ELK; Fail2Ban/ufw на уровне сервера

CodeQL - статический анализ Python/JS. Запускается на push/PR
 
Dependabot - следит за уязвимостями/обновлениями зависимостей (`pip`, `npm`, а также Dockerfile). 

Secret scan (gitleaks) - в CI проверка на утечки секретов


## Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.

## Демо

Проект можно запустить локально следуя инструкциям выше.

---

**Примечание:** Настройки Keycloak и секретные переменные окружения не включены в репозиторий по соображениям безопасности.

**Автор:** Александр Кочетков ([@Werner029](https://github.com/Werner029))
