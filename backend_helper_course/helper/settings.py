import os
from pathlib import Path

from celery.schedules import crontab
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'secret-key')

DEBUG_ENV = os.getenv('DJANGO_DEBUG', 'false').lower()
DEBUG = DEBUG_ENV in ('true', 'yes', '1', 't', 'y')

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')

CSRF_TRUSTED_ORIGINS = [
    'https://hobbymate.ru',
    'https://www.hobbymate.ru',
]

PYTHONIOENCODING = 'utf-8'

INSTALLED_APPS = [
    'django_cleanup.apps.CleanupConfig',
    'sorl.thumbnail',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'storages',
    'django.contrib.gis',
    'pgvector.django',
    'django_extensions',
    'rest_framework',
    'corsheaders',
    'channels',
    'api.apps.ApiConfig',
    'dialogs.apps.DialogsConfig',
    'feedback.apps.FeedbackConfig',
    'users.apps.UsersConfig',
    'interests.apps.InterestsConfig',
    'custom_groups.apps.CustomGroupsConfig',
    'phonenumber_field',
]
INSTALLED_APPS += [
    'drf_spectacular',
    'drf_spectacular_sidecar',
]

AUTH_USER_MODEL = 'users.CustomUser'
if settings.DEBUG:
    INSTALLED_APPS += ('debug_toolbar',)  # pragma: no cover

INTERNAL_IPS = ['172.19.0.1', 'localhost', '127.0.0.1']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'helper.middleware.DRFRequestLogMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]
CORS_ALLOWED_ORIGINS = ['https://hobbymate.ru', 'http://localhost:5173']

CORS_ALLOWED_HEADERS = [
    'authorization',
    'content-type',
    'accept',
    'origin',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'helper.auth.KeycloakJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'HobbyMate API',
    'DESCRIPTION': 'REST && WebSocket API для подбора собеседников',
    'SERVE_INCLUDE_SCHEMA': False,
}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
KEYCLOAK_REALM = 'hobbymate'
KEYCLOAK_BASE_URL = 'http://hobbymate.ru/keycloak'
KEYCLOAK_JWKS_URL = (
    'http://keycloak:8080/keycloak/realms/',
    'hobbymate/protocol/openid-connect/certs',
)

if settings.DEBUG:
    MIDDLEWARE += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )  # pragma: no cover

ROOT_URLCONF = 'helper.urls'

AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'helper.wsgi.application'

REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'DjangoServer',
        'USER': 'postgres',
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'primer'),
        'HOST': os.environ.get('POSTGRES_HOST', 'db'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    },
}

DATABASES['default']['TEST'] = {'TEMPLATE': 'template_test'}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0',
    },
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [
                f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/1',
            ],
        },
    },
}

CELERY_BROKER_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/3'
CELERY_RESULT_BACKEND = (
    f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/4'
)

CELERY_BEAT_SCHEDULE = {
    'deactivate-weekly-inactive': {
        'task': 'users.tasks.deactivate_inactive_users',
        'schedule': crontab(hour=3, minute=0),
    },
    'refresh-groups-every-10m': {
        'task': 'dialogs.tasks.refresh_groups',
        'schedule': 600,
    },
}
TIME_ZONE = 'UTC'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'fmt': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'filters': {
        'trim_body': {
            '()': 'helper.logging_filters.TrimBodyFilter',
            'max_length': 2_000,
        },
        'mask_secrets': {
            '()': 'helper.logging_filters.MaskSecretsFilter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'logstash': {
            'class': 'logstash_async.handler.AsynchronousLogstashHandler',
            'level': 'INFO',
            'host': os.getenv('LOGSTASH_HOST', 'logstash'),
            'port': int(os.getenv('LOGSTASH_PORT', 5959)),
            'database_path': BASE_DIR / 'logstash.db',
            'tcp_keepalive': True,
            'formatter': 'json',
            'filters': ['trim_body', 'mask_secrets'],
        },
    },
    'root': {
        'handlers': ['console', 'logstash'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['logstash'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['logstash'],
            'level': 'WARNING',
            'propagate': False,
        },
        'drf.request': {
            'handlers': ['logstash'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['logstash'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['logstash'],
            'level': 'WARNING',
            'propagate': False,
        },
        'py.warnings': {
            'handlers': ['logstash'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation'
            '.UserAttributeSimilarityValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.MinimumLengthValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation'
            '.CommonPasswordValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation'
            '.NumericPasswordValidator'
        ),
    },
]

LANGUAGES = [
    ('en', _('English')),
    ('ru', _('Russian')),
]

LOCALE_PATHS = (BASE_DIR / 'locale',)

LANGUAGE_CODE = 'en'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATICFILES_DIRS = [
    BASE_DIR / 'static_dev',
]

STATIC_ROOT = '/static/'

STORAGES = {
    'default': {
        'BACKEND': 'helper.storage_backends.MediaStorage',
    },
    'staticfiles': {
        'BACKEND': 'helper.storage_backends.StaticStorage',
    },
}

AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME', 'название_бакета')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_S3_ENDPOINT_URL = 'https://storage.yandexcloud.net'
AWS_S3_REGION_NAME = 'ru-central1'
MEDIA_URL = f'https://storage.yandexcloud.net/{AWS_STORAGE_BUCKET_NAME}/media/'
STATIC_URL = (
    f'https://storage.yandexcloud.net/{AWS_STORAGE_BUCKET_NAME}/static/'
)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': [
            'heading',
            '|',
            'bold',
            'italic',
            'link',
            'bulletedList',
            'numberedList',
            'blockQuote',
            '|',
            'alignment:left',
            'alignment:right',
            'alignment:center',
            'alignment:justify',
            '|',
            'imageUpload',
            '|',
            'undo',
            'redo',
        ],
        'alignment': {'options': ['left', 'right', 'center', 'justify']},
        'height': 300,
        'width': '100%',
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = BASE_DIR / 'sent_emails'
