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
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG")
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

# STORAGE
S3_ENDPOINT_URL = env("S3_ENDPOINT_URL", default="")
S3_ACCESS_KEY = env("S3_ACCESS_KEY", default="")
S3_SECRET_KEY = env("S3_SECRET_KEY", default="")
S3_BUCKET_NAME = env("S3_BUCKET_NAME", default="")
S3_CONFIGURED = all(
    (S3_ENDPOINT_URL, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET_NAME)
)
if DJANGO_ENV == "production" and not S3_CONFIGURED:
    raise ImproperlyConfigured("La configuration S3 est obligatoire en production.")

if S3_CONFIGURED:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "endpoint_url": S3_ENDPOINT_URL,
                "access_key": S3_ACCESS_KEY,
                "secret_key": S3_SECRET_KEY,
                "bucket_name": S3_BUCKET_NAME,
                "default_acl": None,
                "file_overwrite": False,
                "querystring_auth": False,
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

# SECURITY
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = DJANGO_ENV == "production"
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = DJANGO_ENV == "production"
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

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
