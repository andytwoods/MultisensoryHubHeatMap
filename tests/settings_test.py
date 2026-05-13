SECRET_KEY = "test-secret-key-not-for-production"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "concept_analytics",
]
ROOT_URLCONF = "tests.urls"
CONCEPT_ANALYTICS = {
    "ALLOWED_ORIGINS": ["https://storyfutures.github.io"],
    "MAX_EVENTS_PER_BATCH": 50,
    "MAX_PAYLOAD_BYTES": 65536,
    "IDLE_THRESHOLD_SECONDS": 60,
    "SUMMARY_TOKEN": "test-token",
}
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
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
STATIC_URL = "static/"
