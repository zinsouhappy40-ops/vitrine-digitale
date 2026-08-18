import re
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured


# BASE
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(env_file)

DJANGO_ENV = env("DJANGO_ENV")
if DJANGO_ENV not in {"development", "production"}:
    raise ImproperlyConfigured(
        "DJANGO_ENV doit valoir 'development' ou 'production'."
    )
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG")
if DJANGO_ENV == "production" and DEBUG:
    raise ImproperlyConfigured("DJANGO_DEBUG doit être False en production.")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# INSTALLED_APPS
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "storages",
    "apps.accounts",
    "apps.businesses",
    "apps.catalog",
    "apps.storefront",
    "apps.core",
]

# MIDDLEWARE
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# URLS
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# TEMPLATES
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# DATABASE
DATABASES = {
    "default": env.db("DATABASE_URL"),
}
DATABASES["default"]["CONN_MAX_AGE"] = 60
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
DATABASE_SCHEMA = env("DATABASE_SCHEMA", default="")
if DATABASE_SCHEMA:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", DATABASE_SCHEMA):
        raise ImproperlyConfigured("DATABASE_SCHEMA contient un nom invalide.")
    DATABASES["default"].setdefault("OPTIONS", {})["options"] = (
        f"-c search_path={DATABASE_SCHEMA},public"
    )

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "vitrine-digitale",
    }
}

# AUTHENTICATION
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "catalog:dashboard"

# PASSWORDS
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# STATIC
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# MEDIA
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
SERVE_MEDIA_FILES = env.bool("SERVE_MEDIA_FILES", default=DEBUG)

# STORAGE
S3_ENDPOINT_URL = env("S3_ENDPOINT_URL", default="")
S3_ACCESS_KEY = env("S3_ACCESS_KEY", default="")
S3_SECRET_KEY = env("S3_SECRET_KEY", default="")
S3_BUCKET_NAME = env("S3_BUCKET_NAME", default="")
S3_REGION_NAME = env("S3_REGION_NAME", default="")
S3_CONFIGURED = all(
    (S3_ENDPOINT_URL, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET_NAME)
)
USE_S3_STORAGE = env.bool("USE_S3_STORAGE", default=S3_CONFIGURED)
if USE_S3_STORAGE and not S3_CONFIGURED:
    raise ImproperlyConfigured(
        "Les variables S3 sont obligatoires lorsque USE_S3_STORAGE=True."
    )

if USE_S3_STORAGE:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "endpoint_url": S3_ENDPOINT_URL,
                "access_key": S3_ACCESS_KEY,
                "secret_key": S3_SECRET_KEY,
                "bucket_name": S3_BUCKET_NAME,
                "region_name": S3_REGION_NAME or None,
                "default_acl": None,
                "file_overwrite": False,
                "querystring_auth": True,
                "addressing_style": "path",
            },
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": (
                "whitenoise.storage.CompressedManifestStaticFilesStorage"
                if DJANGO_ENV == "production"
                else "django.contrib.staticfiles.storage.StaticFilesStorage"
            ),
        },
    }

# SECURITY
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = DJANGO_ENV == "production"
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = DJANGO_ENV == "production"
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = DJANGO_ENV == "production"
SECURE_HSTS_SECONDS = 31536000 if DJANGO_ENV == "production" else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = DJANGO_ENV == "production"
SECURE_HSTS_PRELOAD = DJANGO_ENV == "production"

# LOCALIZATION
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# LOGGING
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
