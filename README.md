# PyLinkShort

PyLinkShort – сервис сокращения ссылок, позволяющий пользователям создавать, редактировать, удалять и получать аналитику по своим коротким URL. Проект реализован на FastAPI для backend, а также Streamlit для frontend. В качестве бд для сервиса используется PostgreSQL и Redis для кэширования. Сервис поддерживает регистрацию пользователей, создание кастомных alias-ссылок (с возможностью ограничения времени жизни ссылок) и дополнительные функции, например, удаление неиспользуемых ссылок и историю истекших ссылок.

**Пользовательский интерфейс для работы с сервисом представлен на этой странице:** https://pylinkshort-webpage.onrender.com

## Функциональные возможности сервиса

### Обязательные функции ДЗ:
- **Создание, удаление, изменение и получение информации по короткой ссылке:**
  - `POST /api/links` – создание новой ссылки с возможностью указания кастомного alias и времени жизни.
  - `GET /{short_code}` – публичный редирект, который ищет оригинальный URL по short_code и перенаправляет пользователя.
  - `PUT /api/links/{short_code}` – обновление оригинального URL и срока жизни.
  - `DELETE /api/links/{short_code}` – удаление ссылки.
- **Статистика по ссылке:**
  - `GET /api/links/{short_code}/stats` – возвращает оригинальный URL, дату создания, количество переходов и дату последнего использования.
- **Поиск ссылки по оригинальному URL:**
  - `GET /api/links/search?original_url={url}` – поиск записи по исходному URL.
- **Регистрация и управление аккаунтом:**
  - `POST /api/auth/register` – регистрация нового пользователя.
  - `POST /api/auth/login` – вход в систему (с установкой cookie-сессии).
  - `GET /api/auth/profile` – получение профиля текущего пользователя.
  - `DELETE /api/auth/user` – удаление аккаунта (с каскадным удалением всех связанных ссылок).

### Дополнительные функции:
- **Кэширование популярных ссылок:**  
  Redis используется для кэширования данных перенаправления, что ускоряет обработку запросов.
- **Автоматическое удаление неиспользуемых ссылок:**  
  (Функциональность может быть дополнительно реализована в виде фоновой задачи.)
- **Отображение аналитики:**  
  Frontend-часть (на Streamlit) позволяет просматривать статистику переходов по ссылкам (общее количество переходов, построение графиков).

## Стэк сервиса

- **Backend:** FastAPI, Uvicorn, SQLAlchemy, psycopg2, python-dotenv, passlib, Redis, Pydantic.
- **Frontend:** Streamlit, Requests, Pandas.
- **База данных:** PostgreSQL (Render Managed PostgreSQL в продакшене).
- **Кэширование:** Redis.
- **Контейнеризация:** Docker, Docker Compose.

## Структура проекта

```
PyLinkShort/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env              # Для локального тестирования
│   └── app/
│       ├── init.py
│       ├── main.py
│       ├── api/
│       │   ├── init.py
│       │   ├── auth.py
│       │   └── links.py
│       ├── core/
│       │   ├── init.py
│       │   ├── cache.py
│       │   ├── config.py
│       │   ├── database.py
│       │   └── security.py
│       ├── models/
│       │   ├── init.py
│       │   ├── user.py
│       │   └── link.py
│       ├── schemas/
│       │   ├── init.py
│       │   ├── user.py
│       │   └── link.py
│       └── services/
│           ├── init.py
│           ├── analytics.py
│           └── shortener.py
├── frontend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── secrets.toml      # Для локального тестирования
│   └── app.py
├── docker-compose.yml    # Для локального тестирования
└── README.md
```

## Локальное тестирование

1. **Настройка переменных окружения для локального запуска:**  
   В файле `backend/.env` укажите следующие значения по шаблону:
   ```env
   DATABASE_URL=postgresql://urlshort:urlshortpass@localhost:5432/urlshort_db
   REDIS_URL=redis://localhost:6379/0
   SECRET_KEY=YOUR_SECRET_KEY
   SESSION_TTL=86400
   INACTIVITY_DAYS=90
   ```
   
Важно, чтобы PostgreSQL и Redis были запущены на локальной машине.

2.	**Отдельный запуск backend:**
Перейдите в папку backend и выполните:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API будет доступно по ссылке http://localhost:8000 в случае локального тестирования

3.	**Отдельный запуск frontend:**
Перейдите в папку frontend и выполните:

```bash
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

Frontend-приложение будет доступно по ссылке http://localhost:8501 в случае локального тестирования.

4. **Docker Compose**

Для сборки сервиса воедино был написан docker-compose.yml файл для локального тестирования.

Запустить все сервисы можно командой:

```bash
docker-compose up --build
```

## Deploy на Render

Проект был задеплойен в интернет с помощью платформы [Render](https://dashboard.render.com/). 
На основе кода этого репозитория, в этой платформе было развернуто 4 компонента сервиса:

1. FastAPI сервис (backend): API_URL: "https://pythondz3.onrender.com"
2. StreamLit сервис (frontend, пользовательский интерфейс): [PyLinkShort_webpage](https://pythondz3frontend.onrender.com)
3. PostgreSQL DB: `postgresql://@dpg-cvl8hgp5pdvs73daaf90-a.oregon-postgres.render.com:5432/links_as1r`
4. Redis (key-value store): `redis://red-cvl9mdadbo4c73d96sp0:6379`
