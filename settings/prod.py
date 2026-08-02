from .base import *
import os
DEBUG = False
ALLOWED_HOSTS = ['*']


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

# Allow DATABASE_URL environment variable to configure the production database.
# Prefer `dj_database_url` when available, otherwise fall back to a simple parser.
db_url = os.environ.get('DB_URI') or os.environ.get('DB_URI')
if db_url:
    try:
        import dj_database_url

        DATABASES['default'] = dj_database_url.parse(db_url, conn_max_age=600, ssl_require=True)
    except Exception:
        # Minimal fallback parsing for common schemes (postgres, mysql, sqlite)
        from urllib.parse import urlparse

        result = urlparse(db_url)
        scheme = result.scheme.split('+')[0]
        if scheme in ('sqlite', 'sqlite3'):
            # sqlite: use file path
            path = result.path or ':memory:'
            DATABASES['default'] = {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': path,
            }
        else:
            engine_map = {
                'postgres': 'django.db.backends.postgresql',
                'postgresql': 'django.db.backends.postgresql',
                'mysql': 'django.db.backends.mysql',
            }
            engine = engine_map.get(scheme, 'django.db.backends.postgresql')
            DATABASES['default'] = {
                'ENGINE': engine,
                'NAME': (result.path or '').lstrip('/'),
                'USER': result.username or '',
                'PASSWORD': result.password or '',
                'HOST': result.hostname or '',
                'PORT': result.port or '',
            }


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',  # captures every request + errors
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # set to DEBUG to see every SQL query
            'propagate': False,
        },
    },
}


SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# Production caching configuration using Redis (Render)
redis_url = os.environ.get("REDIS_URL")
if redis_url:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": redis_url,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }

