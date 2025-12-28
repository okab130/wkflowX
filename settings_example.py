# Django settings.py に追加する設定（製造業・建設業向けワークフローシステム）

# ========================================
# メール設定
# ========================================

# 開発環境: コンソールにメール出力
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# 本番環境: SMTP設定例
"""
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # または企業のSMTPサーバー
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'  # 環境変数で管理すること
DEFAULT_FROM_EMAIL = 'noreply@example.com'
"""

# サイトURL（メール通知用）
SITE_URL = 'http://localhost:8000'  # 本番環境では実際のURLに変更

# デフォルト送信元メールアドレス
DEFAULT_FROM_EMAIL = 'workflow-system@example.com'


# ========================================
# アプリケーション設定
# ========================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'workflow',  # ワークフローアプリケーション
]

# ========================================
# 国際化・ローカライゼーション
# ========================================

LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True

# 日付フォーマット
DATE_FORMAT = 'Y年m月d日'
DATETIME_FORMAT = 'Y年m月d日 H:i'
SHORT_DATE_FORMAT = 'Y/m/d'
SHORT_DATETIME_FORMAT = 'Y/m/d H:i'

# ========================================
# メディアファイル設定（添付ファイル用）
# ========================================

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ファイルアップロード設定
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# ========================================
# 静的ファイル設定
# ========================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ========================================
# セキュリティ設定
# ========================================

# 本番環境では必ず設定すること
"""
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
"""

# CSRF信頼済みオリジン（本番環境で設定）
# CSRF_TRUSTED_ORIGINS = ['https://your-domain.com']

# ========================================
# ログイン・認証設定
# ========================================

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/workflow/'
LOGOUT_REDIRECT_URL = '/'

# パスワード検証
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ========================================
# データベース設定例
# ========================================

# SQLite（開発環境）
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# PostgreSQL（本番環境推奨）
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'workflow_db',
        'USER': 'workflow_user',
        'PASSWORD': 'your-password',  # 環境変数で管理すること
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
"""

# ========================================
# ログ設定
# ========================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'workflow.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'workflow': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}

# logsディレクトリの作成
LOGS_DIR = BASE_DIR / 'logs'
if not LOGS_DIR.exists():
    LOGS_DIR.mkdir()

# ========================================
# キャッシュ設定（パフォーマンス向上）
# ========================================

# 開発環境
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# 本番環境（Redis推奨）
"""
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
"""

# ========================================
# セッション設定
# ========================================

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 3600  # 1時間（秒単位）
SESSION_SAVE_EVERY_REQUEST = True

# ========================================
# ページネーション設定
# ========================================

# 1ページあたりの表示件数
PAGINATE_BY = 20

# ========================================
# 環境変数の読み込み例
# ========================================

"""
# .envファイルから環境変数を読み込む場合
# pip install python-decouple

from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

DATABASE_URL = config('DATABASE_URL')
"""
