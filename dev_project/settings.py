from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Development only — never use this key in production
SECRET_KEY = "dev-only-not-for-production-replace-before-deploying"
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "concept_analytics",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "dev_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "dev.sqlite3",
    }
}

STATIC_URL = "static/"

LOGIN_URL = "/admin/login/"

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
]

CONCEPT_ANALYTICS = {
    "ALLOWED_ORIGINS": [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://storyfutures.github.io",
    ],
    "MAX_EVENTS_PER_BATCH": 50,
    "MAX_PAYLOAD_BYTES": 65536,
    "IDLE_THRESHOLD_SECONDS": 60,
    "SUMMARY_TOKEN": "dev-token",
}
