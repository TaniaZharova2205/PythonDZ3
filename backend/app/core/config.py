import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")
SESSION_TTL = int(os.getenv("SESSION_TTL", "86400"))
INACTIVITY_DAYS = int(os.getenv("INACTIVITY_DAYS", "90"))