import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# GARANTE QUE A PASTA DE LOGS SEJA CRIADA SE NÃO EXISTIR (Evita o erro anterior)
LOG_DIR = BASE_DIR / 'logs'
if not LOG_DIR.exists():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-MUDE-ISSO-EM-PRODUCAO-use-uma-chave-forte-aqui')

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost 127.0.0.1').split()

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.SecurityHeadersMiddleware',
    'core.middleware.RateLimitMiddleware',
]

# AJUSTADO PARA O NOME CORRETO DA SUA PASTA NO WINDOWS
ROOT_URLCONF = 'Conexao_cidada.urls'

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
            ],
        },
    },
]

# AJUSTADO PARA O NOME CORRETO DA SUA PASTA NO WINDOWS
WSGI_APPLICATION = 'Conexao_cidada.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ─── AUTENTICAÇÃO ───────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'core.Usuario'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# ─── SESSÃO ─────────────────────────────────────────────────────────────────
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG        # True em produção (HTTPS)
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 3600               # 1 hora
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ─── CSRF ───────────────────────────────────────────────────────────────────
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = 'Lax'

# ─── SEGURANÇA HTTP ─────────────────────────────────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True

# ─── ESTÁTICOS ──────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── LOGGING ────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{levelname} {asctime} {module} {message}', 'style': '{'},
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': LOG_DIR / 'django.log',
            'formatter': 'verbose',
        },
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {'handlers': ['console'], 'level': 'DEBUG' if DEBUG else 'WARNING'},
    'loggers': {
        'django.security': {'handlers': ['file', 'console'], 'level': 'WARNING', 'propagate': False},
    },
}

# ─── MENSAGENS DE ERRO ──────────────────────────────────────────────────────
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'