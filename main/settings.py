# type: ignore[reportAttributeAccessIssue]
import os
import socket
import sys
from pathlib import Path

import environ

from main.logging import log_render_extra_context
from main.sentry import SentryConfig
from utils.firebase import FirebaseHelper
from utils.git import GitHelper

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


env = environ.Env(
    # Django
    DEBUG=(bool, False),
    ENABLE_DEBUG_TOOLBAR=(bool, False),
    SECRET_KEY=str,
    ADDITIONAL_ALLOWED_HOSTS=(list, []),  # Eg: api.example.org
    APP_ENVIRONMENT=str,  # DEV, STAGE, PROD
    APP_TYPE=str,  # WEB, WORKER, WORKER-BEAT
    APP_RELEASE=(str, None),  # As fallback we will try to use .git/HEAD
    APP_LOG_LEVEL=(str, "INFO"),
    # Domain configs
    APP_DOMAIN=str,  # Eg: https://api.example.org
    FRONTEND_DOMAIN=str,  # Eg: https://web.example.org
    SESSION_COOKIE_DOMAIN=str,  # .example.com
    CSRF_COOKIE_DOMAIN=str,  # .example.com
    MAPSWIPE_ADDITIONAL_TRUSTED_ORIGINS=(list, []),  # https://app1.example.com,https://app2.example.com
    # NOTE: Changing TIME_ZONE will break celery periodic tasks https://django-celery-beat.readthedocs.io/en/latest/#important-warning-about-time-zones
    TIME_ZONE=(str, "UTC"),
    # Database
    POSTGRES_DB=str,
    POSTGRES_USER=str,
    POSTGRES_PASSWORD=str,
    POSTGRES_HOST=str,
    POSTGRES_PORT=(int, 5432),
    # Storage
    MEDIA_URL=(str, "media/"),
    STATIC_URL=(str, "static/"),
    TEMP_DIR=(str, "/tmp/"),  # noqa: S108
    # -- S3 storage
    AWS_S3_ENABLED=(bool, False),
    AWS_S3_ENDPOINT_URL=(str, None),
    AWS_S3_ACCESS_KEY_ID=str,
    AWS_S3_SECRET_ACCESS_KEY=str,
    AWS_S3_REGION_NAME=str,
    AWS_S3_MEDIA_BUCKET_NAME=str,
    AWS_S3_STATIC_BUCKET_NAME=str,
    # -- Filesystem (default) XXX: Don't use in production
    MEDIA_ROOT=(str, BASE_DIR / "data/media"),
    STATIC_ROOT=(str, BASE_DIR / "data/static"),
    # Email
    EMAIL_HOST=str,
    EMAIL_SUBJECT_PREFIX=(str, "Mapswipe:"),
    EMAIL_USE_TLS=(bool, True),
    EMAIL_PORT=(int, 587),
    EMAIL_HOST_USER=str,
    EMAIL_HOST_PASSWORD=str,
    DEFAULT_FROM_EMAIL=str,
    # Celery
    CELERY_REDIS_URL=str,  # redis://redis:6379/0
    # Cache
    CACHE_REDIS_URL=str,  # redis://redis:6379/1
    TEST_CACHE_REDIS_URL=(str, None),  # redis://redis:6379/11
    # Sentry
    SENTRY_ENABLED=(bool, False),
    SENTRY_DEBUG=(bool, False),
    SENTRY_DSN=(str, None),
    SENTRY_MONITOR_CELERY_BEAT_TASKS=(bool, True),
    SENTRY_TRACES_SAMPLE_RATE=(float, 0.2),
    SENTRY_PROFILE_SAMPLE_RATE=(float, 0.2),
    # Map Image keys
    MAP_IMAGE_BING_API_KEY=str,
    MAP_IMAGE_MAPBOX_API_KEY=str,
    MAP_IMAGE_MAXAR_STANDARD_API_KEY=str,
    MAP_IMAGE_MAXAR_PREMIUM_API_KEY=str,
    MAP_IMAGE_ESRI_API_KEY=str,
    MAP_IMAGE_ESRI_BETA_API_KEY=str,
    OSMCHA_API_KEY=str,  # os.environ["OSMCHA_API_KEY"]
    # MAP_IMAGE_DIGITAL_GLOBE_API_KEY=str,
    # Firebase
    FIREBASE_EMULATOR_USE=(bool, False),
    # -- Emulator (If FIREBASE_EMULATOR_USE is True)
    # -- NOTE: Using non standard emulator ENV variable for enabling firebase emulator
    #    to allow custom logics to enable/disable emulator use by firebase-admin
    FIREBASE_EMULATOR_PROJECT_ID=str,  # FIREBASE_DB_URL also uses this value
    FIREBASE_EMULATOR_DATABASE_HOST=str,
    FIREBASE_EMULATOR_TEST_HOST=(str, None),
    # -- Real (If FIREBASE_EMULATOR_USE is False)
    FIREBASE_DB_URL=str,  # https://mapswipe-dev.firebaseio.com
    FIREBASE_CREDENTIALS_B64_GZ=(str, None),  # gzip -cn credential.json | base64 -w 0
    GOOGLE_APPLICATION_CREDENTIALS=str,
    # Pytest
    PYTEST_XDIST_WORKER=(str, None),
)

GIT_HELPER = GitHelper(BASE_DIR)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

APP_LOG_LEVEL = env("APP_LOG_LEVEL")
APP_DOMAIN = env.url("APP_DOMAIN")
FRONTEND_DOMAIN = env.url("FRONTEND_DOMAIN")
APP_ENVIRONMENT = env("APP_ENVIRONMENT").upper()
APP_TYPE = env("APP_TYPE").upper()
APP_RELEASE = env("APP_RELEASE") or GIT_HELPER.commit_sha
SECRET_KEY = env("SECRET_KEY")

DEBUG = env("DEBUG")

ALLOWED_HOSTS = [
    APP_DOMAIN.hostname,
    *env("ADDITIONAL_ALLOWED_HOSTS"),
]

# See if we are inside a test environment (pytest)
IS_TESTING = (
    any(
        [
            arg in sys.argv
            for arg in [
                "test",
                "pytest",
                "/usr/local/bin/pytest",
                "py.test",
                "/usr/local/bin/py.test",
                "/usr/local/lib/python3.6/dist-packages/py/test.py",
            ]
            # Provided by pytest-xdist
        ],
    )
    or env("PYTEST_XDIST_WORKER") is not None
)

# Application definition

INSTALLED_APPS = [
    # Core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    # External
    "strawberry_django",
    "corsheaders",
    "django_premailer",
    "django_celery_beat",
    "djangoql",
    # - Health-check
    "health_check",  # required
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    "health_check.contrib.migrations",
    "health_check.contrib.redis",  # requires Redis broker
    # Internal
    "apps.common",
    "apps.user",
    "apps.project",
    "apps.tutorial",
    "apps.contributor",
    "apps.mapping",
    "apps.community_dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "main.middlewares.sentry_middleware",
]

ROOT_URLCONF = "main.urls"

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

WSGI_APPLICATION = "main.wsgi.application"

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": env("POSTGRES_PORT"),
    },
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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

AUTH_USER_MODEL = "user.User"

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = env("TIME_ZONE")

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

TEMP_DIR = env("TEMP_DIR")
MEDIA_URL = env("MEDIA_URL")
STATIC_URL = env("STATIC_URL")

if env("AWS_S3_ENABLED"):
    AWS_S3_CONFIG_OPTIONS = {
        "endpoint_url": env("AWS_S3_ENDPOINT_URL"),
        "access_key": env("AWS_S3_ACCESS_KEY_ID"),
        "secret_key": env("AWS_S3_SECRET_ACCESS_KEY"),
        "region_name": env("AWS_S3_REGION_NAME"),
    }

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                **AWS_S3_CONFIG_OPTIONS,
                "bucket_name": env("AWS_S3_MEDIA_BUCKET_NAME"),
                "location": "media/",
                "file_overwrite": False,
            },
        },
        "staticfiles": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                **AWS_S3_CONFIG_OPTIONS,
                "bucket_name": env("AWS_S3_STATIC_BUCKET_NAME"),
                "querystring_auth": False,
                "location": "static/",
                "file_overwrite": True,
            },
        },
    }

else:
    # Filesystem
    MEDIA_ROOT = env("MEDIA_ROOT")
    STATIC_ROOT = env("STATIC_ROOT")


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email config
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_SUBJECT_PREFIX = env("EMAIL_SUBJECT_PREFIX")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

PREMAILER_OPTIONS = dict(
    disable_validation=not DEBUG,  # Enable validation in DEBUG only
)

# Redis lock
REDIS_LOCK_EXPIRE = 60 * 10  # Lock expires in 10min (in seconds)

# Cache
CACHE_REDIS_URL = env("CACHE_REDIS_URL")
TEST_CACHE_REDIS_URL = env("TEST_CACHE_REDIS_URL")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": CACHE_REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "local-memory": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        },
    },
}

# Celery
CELERY_RESULT_BACKEND = CELERY_BROKER_URL = env("CELERY_REDIS_URL")
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_SOFT_TIME_LIMIT = 30 * 60  # 30 mins max (To tackle worst cases)
CELERY_TASK_TIME_LIMIT = 35 * 60
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = False

# HEALTH-CHECK
REDIS_URL = CACHE_REDIS_URL
HEALTHCHECK_CACHE_KEY = "mapswipe_healthcheck_key"

# Security Header configuration

MAPSWIPE_TRUSTED_ORIGINS = [
    APP_DOMAIN.geturl(),
    FRONTEND_DOMAIN.geturl(),
    *env("MAPSWIPE_ADDITIONAL_TRUSTED_ORIGINS"),
]

SESSION_COOKIE_NAME = f"MAPSWIPE-{APP_ENVIRONMENT}-SESSIONID"
CSRF_COOKIE_NAME = f"MAPSWIPE-{APP_ENVIRONMENT}-CSRFTOKEN"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
CSP_DEFAULT_SRC = ["'self'"]
SECURE_REFERRER_POLICY = "same-origin"
if APP_DOMAIN.scheme == "https":
    SESSION_COOKIE_NAME = f"__Secure-{SESSION_COOKIE_NAME}"
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SECURE_HSTS_SECONDS = 30  # TODO(thenav56): Increase this slowly
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CSRF_TRUSTED_ORIGINS = MAPSWIPE_TRUSTED_ORIGINS

# -- https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-SESSION_COOKIE_DOMAIN
SESSION_COOKIE_DOMAIN = env("SESSION_COOKIE_DOMAIN")
# https://docs.djangoproject.com/en/3.2/ref/settings/#csrf-cookie-domain
CSRF_COOKIE_DOMAIN = env("CSRF_COOKIE_DOMAIN")


# CORS
CORS_ALLOWED_ORIGINS = MAPSWIPE_TRUSTED_ORIGINS

CORS_ALLOW_CREDENTIALS = True
CORS_URLS_REGEX = r"(^/media/.*$)|(^/graphql/$)|(^/health-check/$)"
CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
)

CORS_ALLOW_HEADERS = (
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    # Required by sentry
    "sentry-trace",
    "baggage",
)


# Sentry Config
SENTRY_ENABLED = env("SENTRY_ENABLED")

if SENTRY_ENABLED:
    SENTRY_CONFIG = SentryConfig(
        dsn=env("SENTRY_DSN"),
        debug=env("SENTRY_DEBUG"),
        app_type=APP_TYPE,
        release=APP_RELEASE,
        environment=APP_ENVIRONMENT,
        send_default_pii=True,
        traces_sample_rate=env("SENTRY_TRACES_SAMPLE_RATE"),
        profiles_sample_rate=env("SENTRY_PROFILE_SAMPLE_RATE"),
        # Custom configs
        tags={"site": APP_DOMAIN.geturl()},
        monitor_celery_beat_tasks=env("SENTRY_MONITOR_CELERY_BEAT_TASKS"),
    )
    SENTRY_CONFIG.init_sentry()

# Strawberry
STRAWBERRY_DJANGO = {
    "FIELD_DESCRIPTION_FROM_HELP_TEXT": True,
    "TYPE_DESCRIPTION_FROM_MODEL_DOCSTRING": True,
    "MUTATIONS_DEFAULT_HANDLE_ERRORS": True,
    "PAGINATION_DEFAULT_LIMIT": 20,
    "DEFAULT_PK_FIELD_NAME": "id",
}

# MAP_IMAGE_KEYs
MAP_IMAGE_BING_API_KEY = env("MAP_IMAGE_BING_API_KEY")
MAP_IMAGE_MAPBOX_API_KEY = env("MAP_IMAGE_MAPBOX_API_KEY")
MAP_IMAGE_MAXAR_STANDARD_API_KEY = env("MAP_IMAGE_MAXAR_STANDARD_API_KEY")
MAP_IMAGE_MAXAR_PREMIUM_API_KEY = env("MAP_IMAGE_MAXAR_PREMIUM_API_KEY")
MAP_IMAGE_ESRI_API_KEY = env("MAP_IMAGE_ESRI_API_KEY")
MAP_IMAGE_ESRI_BETA_API_KEY = env("MAP_IMAGE_ESRI_BETA_API_KEY")
# MAP_IMAGE_DIGITAL_GLOBE_API_KEY = env("MAP_IMAGE_DIGITAL_GLOBE_API_KEY")

OSMCHA_API_KEY = env("OSMCHA_API_KEY")

# Firebase
FIREBASE_EMULATOR_USE = env("FIREBASE_EMULATOR_USE")
FIREBASE_EMULATOR_TEST_HOST = env("FIREBASE_EMULATOR_TEST_HOST")
FIREBASE_CREDENTIALS_B64_GZ = env("FIREBASE_CREDENTIALS_B64_GZ")
if FIREBASE_EMULATOR_USE:
    # NOTE: Adding environment variable programmatically
    os.environ["FIREBASE_DATABASE_EMULATOR_HOST"] = env.url("FIREBASE_EMULATOR_DATABASE_HOST").geturl()
    os.environ["GCLOUD_PROJECT"] = env("FIREBASE_EMULATOR_PROJECT_ID")
    FIREBASE_DB_URL = "https://" + env("FIREBASE_EMULATOR_PROJECT_ID")
else:
    FIREBASE_DB_URL = env.url("FIREBASE_DB_URL").geturl()

FIREBASE_HELPER = FirebaseHelper(
    FIREBASE_DB_URL,
    credential_b64_gz=FIREBASE_CREDENTIALS_B64_GZ,
    using_emulator=FIREBASE_EMULATOR_USE,
)


# TODO(thenav56): Handle file logs using gunicorn
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "render_extra_context": {
            "()": "django.utils.log.CallbackFilter",
            "callback": log_render_extra_context,
        },
    },
    "formatters": {
        "simple": {
            "format": ("%(asctime)s: - %(threadName)s/%(levelname)s - %(name)s - %(message)s %(context)s"),
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "filters": ["render_extra_context"],
        },
    },
    "loggers": {
        **{
            app: {
                "level": env("APP_LOG_LEVEL"),
                "handlers": ["console"],
                "propagate": False,
            }
            for app in ["apps", "main", "utils", "celery", "django"]
        },
    },
    "root": {
        "level": env("APP_LOG_LEVEL"),
        "handlers": ["console"],
    },
}

if DEBUG:
    LOGGING = {
        **LOGGING,
        "formatters": {
            **LOGGING["formatters"],
            "colored_verbose": {
                "()": "colorlog.ColoredFormatter",
                "format": (
                    "%(log_color)s%(asctime)s: %(threadName)s - %(levelname)-s%(red)s %(module)-s%(reset)s "
                    "%(blue)s%(message)s %(context)s"
                ),
            },
        },
        "handlers": {
            **LOGGING["handlers"],
            "colored_console": {
                "class": "logging.StreamHandler",
                "formatter": "colored_verbose",
                "filters": ["render_extra_context"],
            },
        },
        "loggers": {
            **{
                key: {
                    **logger,
                    "handlers": ["colored_console"],
                }
                for key, logger in LOGGING["loggers"].items()
            },
        },
        "root": {
            "level": env("APP_LOG_LEVEL"),
            "handlers": ["colored_console"],
        },
    }


# Django toolbar
ENABLE_DEBUG_TOOLBAR = env("ENABLE_DEBUG_TOOLBAR")

if ENABLE_DEBUG_TOOLBAR and not IS_TESTING:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.append("strawberry_django.middlewares.debug_toolbar.DebugToolbarMiddleware")
    INTERNAL_IPS = [
        "127.0.0.1",
        ".".join(socket.gethostbyname(socket.gethostname()).rsplit(".")[:-1]) + ".1",
    ]

# Manual checks
import main.checks  # noqa: F401 E402
